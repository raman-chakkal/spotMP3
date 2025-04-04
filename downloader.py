import os
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Thread
from PyQt6.QtCore import QThread, pyqtSignal
from spotify_utils import authenticate_spotify, get_all_playlist_tracks, sanitize_name, write_download_results
import time


class WriteWorker(Thread):
    """
    A worker thread to handle post-download processing of files.
    """
    def __init__(self, write_queue):
        super().__init__()
        self.write_queue = write_queue
        self.stop_flag = False

    def run(self):
        while not self.stop_flag or not self.write_queue.empty():
            try:
                file_path, _ = self.write_queue.get(timeout=1)
                if not os.path.exists(file_path):
                    logging.error(f"[ERROR] File not found during post-processing: {file_path}")
                else:
                    logging.info(f"[INFO] Post-processing file: {file_path}")
                    # Perform any additional processing here (e.g., metadata updates)
                self.write_queue.task_done()
            except Exception as e:
                logging.error(f"[ERROR] Error during post-processing: {e}")

    def stop(self):
        self.stop_flag = True


class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)  # Progress bar
    status_signal = pyqtSignal(str)  # Status messages

    def __init__(self, playlist_url, download_folder, quality):
        super().__init__()
        self.playlist_url = playlist_url
        self.download_folder = download_folder
        self.quality = quality
        self.cancel_flag = False

    def run(self):
        """Main method to handle the download process."""
        sp = self.authenticate_spotify()
        if not sp:
            self.status_signal.emit("[ERROR] Spotify authentication failed.")
            return

        tracks = self.fetch_playlist_tracks(sp)
        if not tracks:
            self.status_signal.emit("[ERROR] No tracks found.")
            return

        playlist_name = sanitize_name(sp.playlist(self.playlist_url)["name"])
        download_folder = self.create_download_folder(playlist_name)

        total_tracks = len(tracks)
        self.status_signal.emit(f"Downloading {total_tracks} tracks...")

        success_tracks, failed_tracks = self.download_tracks(tracks, download_folder)

        # Write the results to a JSON file
        write_download_results(download_folder, success_tracks, failed_tracks)

        self.status_signal.emit("✅ Download complete!")

    def authenticate_spotify(self):
        """Authenticate with Spotify."""
        return authenticate_spotify()

    def fetch_playlist_tracks(self, sp):
        """Fetch all tracks from the Spotify playlist."""
        return get_all_playlist_tracks(sp, self.playlist_url)

    def create_download_folder(self, playlist_name):
        """Create a folder for the playlist downloads."""
        folder_path = os.path.join(self.download_folder, playlist_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def download_tracks(self, tracks, download_folder):
        """Download all tracks in the playlist."""
        success_tracks = []
        failed_tracks = []

        # Initialize the write queue and worker
        write_queue = Queue()
        write_worker = WriteWorker(write_queue)
        write_worker.start()

        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.download_track, track["track"], download_folder, write_queue): track
                for track in tracks
            }

            for i, future in enumerate(as_completed(futures)):
                if self.cancel_flag:
                    self.status_signal.emit("❌ Download cancelled!")
                    write_worker.stop()
                    return success_tracks, failed_tracks

                try:
                    result = future.result()
                    if result["status"] == "Downloaded":
                        success_tracks.append(result["track"])
                    else:
                        failed_tracks.append({
                            "track": result["track"],
                            "error": result.get("error", "Unknown error")
                        })

                    self.status_signal.emit(f"✔ {result['track']}: {result['status']}")
                    self.progress_signal.emit(int((i + 1) / len(tracks) * 100))
                except Exception as e:
                    logging.error(f"[ERROR] Error processing future result: {e}")

                # Add a small delay to avoid overwhelming the system
                time.sleep(0.5)

        # Wait for all write operations to complete
        write_queue.join()
        write_worker.stop()

        return success_tracks, failed_tracks

    def download_track(self, track, download_folder, write_queue, retries=3):
        """Download a single track."""
        sanitized_track = sanitize_name(track["name"])
        artist = sanitize_name(track["artists"][0]["name"])

        # Check if already downloaded
        if self.is_track_downloaded(download_folder, sanitized_track, artist):
            return {"track": f"{sanitized_track} - {artist}", "status": "Already Downloaded"}

        # Construct the search query
        search_query = f"{track['name']} {track['artists'][0]['name']} {track['album']['name']}"
        command = f'spotdl download "{search_query}" --output "{download_folder}" --bitrate {self.quality} --preload'

        for attempt in range(retries):
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                logging.info(f"[INFO] spotdl stdout: {result.stdout}")
                logging.error(f"[ERROR] spotdl stderr: {result.stderr}")

                if result.returncode == 0:
                    file_path = os.path.join(download_folder, f"{sanitized_track} - {artist}.mp3")
                    if os.path.exists(file_path):
                        write_queue.put((file_path, None))  # Add file to the write queue
                        return {"track": f"{sanitized_track} - {artist}", "status": "Downloaded"}
                    else:
                        logging.error(f"[ERROR] File not found after download: {file_path}")
            except Exception as e:
                logging.error(f"[ERROR] Attempt {attempt + 1}: Error downloading {sanitized_track} - {artist}: {e}")

        return {"track": f"{sanitized_track} - {artist}", "status": "Failed", "error": "Download failed after retries"}

    def is_track_downloaded(self, download_folder, sanitized_track, artist):
        """Check if the track is already downloaded."""
        existing_files = [
            f for f in os.listdir(download_folder)
            if sanitized_track in f and artist in f and f.endswith(".mp3")
        ]
        return bool(existing_files)

    def cancel(self):
        """Cancel the download process."""
        self.cancel_flag = True