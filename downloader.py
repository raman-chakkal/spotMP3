import os
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal
from spotify_utils import authenticate_spotify, get_all_playlist_tracks, sanitize_name, write_download_results
import time


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

        # Use ThreadPoolExecutor for parallel downloads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.download_track, track["track"], download_folder): track
                for track in tracks
            }

            for i, future in enumerate(as_completed(futures)):
                if self.cancel_flag:
                    self.status_signal.emit("❌ Download cancelled!")
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

        return success_tracks, failed_tracks

    def download_track(self, track, download_folder, retries=3):
        """Download a single track."""
        track_name = track["name"]  # Use the original track name
        artist_name = track["artists"][0]["name"]  # Use the original artist name

        # Check if already downloaded
        if self.is_track_downloaded(download_folder, track_name, artist_name):
            return {"track": f"{track_name} - {artist_name}", "status": "Already Downloaded"}

        # Construct the search query
        search_query = f"{track_name} {artist_name} {track['album']['name']}"
        command = f'spotdl download "{search_query}" --output "{download_folder}" --bitrate {self.quality} --preload'

        for attempt in range(retries):
            try:
                logging.info(f"[INFO] Running command: {command}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                logging.info(f"[INFO] spotdl stdout: {result.stdout}")
                logging.error(f"[ERROR] spotdl stderr: {result.stderr}")

                if result.returncode == 0:
                    # Search for the downloaded file in the folder
                    downloaded_file = self.find_downloaded_file(download_folder, track_name, artist_name)
                    if downloaded_file:
                        return {"track": f"{track_name} - {artist_name}", "status": "Downloaded"}
                    else:
                        logging.warning(f"[WARNING] File not found after download: {track_name} - {artist_name}")
                else:
                    logging.error(f"[ERROR] spotdl failed with return code {result.returncode}")
            except Exception as e:
                logging.error(f"[ERROR] Attempt {attempt + 1}: {e}")
            time.sleep(2)  # Add a delay before retrying

        return {"track": f"{track_name} - {artist_name}", "status": "Failed", "error": "Download failed after retries"}

    def is_track_downloaded(self, download_folder, track_name, artist_name):
        """Check if the track is already downloaded."""
        existing_files = [
            f for f in os.listdir(download_folder)
            if track_name in f and artist_name in f and f.endswith(".mp3")
        ]
        return bool(existing_files)

    def find_downloaded_file(self, download_folder, track_name, artist_name):
        """
        Search for a downloaded file in the folder that matches the track and artist name.

        :param download_folder: The folder where the file is expected to be downloaded.
        :param track_name: The original track name from Spotify.
        :param artist_name: The original artist name from Spotify.
        :return: The file path if found, otherwise None.
        """
        try:
            for file_name in os.listdir(download_folder):
                # Check if the file name contains the original track and artist name
                if track_name in file_name and artist_name in file_name and file_name.endswith(".mp3"):
                    return os.path.join(download_folder, file_name)
        except Exception as e:
            logging.error(f"[ERROR] Error searching for downloaded file: {e}")
        return None

    def cancel(self):
        """Cancel the download process."""
        self.cancel_flag = True