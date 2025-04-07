SpotMP3 - Spotify MP3 Downloader

SpotMP3 is a Python-based application that allows users to download Spotify playlists as MP3 files. It uses the Spotify API to fetch playlist details and spotdl to download the tracks. The application features a user-friendly GUI built with PyQt6.

------------------------------------------------------------

FEATURES

- Download Spotify Playlists: Fetch and download all tracks from a Spotify playlist.
- Customizable Quality: Choose the desired audio quality (128k, 192k, 256k, 320k).
- Progress Tracking: View download progress with a progress bar.
- Error Handling: Logs errors for failed downloads and writes results to a JSON file.
- Graphical User Interface (GUI): Built using PyQt6 for an intuitive user experience.
- Retry Logic: Automatically retries failed downloads up to 3 times.
- File Matching: Matches downloaded files using the original Spotify track and artist names.

------------------------------------------------------------

REQUIREMENTS

- Python 3.9 or higher
- Spotify Developer Account (for API credentials)
- FFmpeg (required by spotdl)

------------------------------------------------------------

INSTALLATION

1. Clone the Repository:
   git clone https://github.com/your-username/spotmp3.git
   cd spotmp3

2. Set Up a Virtual Environment:
   python -m venv .venv
   source .venv/bin/activate        (On Windows: .venv\Scripts\activate)

3. Install Dependencies:
   pip install -r requirements.txt

4. Install FFmpeg:
   - Download FFmpeg from https://ffmpeg.org/download.html
   - Add the "bin" folder of FFmpeg to your system PATH

5. Set Up Spotify API Credentials:
   - Create a config.ini file in the project directory with the following content:
     [spotify]
     client_id = your_spotify_client_id
     client_secret = your_spotify_client_secret

------------------------------------------------------------

USAGE

Run the Application:
   python main.py

Steps to Download a Playlist:
1. Enter the Spotify playlist URL in the input field.
2. Select a folder to save the downloaded files.
3. Choose the desired audio quality from the dropdown.
4. Click the "Start Download" button to begin.
5. Cancel a Download: Click the "Cancel" button to stop the ongoing download process.

------------------------------------------------------------

FILE STRUCTURE

- downloader.py         # Logic for downloading playlists
- main.py               # GUI logic using PyQt6
- config.ini            # Spotify API credentials (created by user)
- requirements.txt      # Dependencies
- README.txt            # Project documentation

------------------------------------------------------------

LOGGING

Logs are displayed in the console for debugging purposes. Errors and warnings are logged for:
- Missing files after download
- Spotify API authentication issues
- Failed downloads

------------------------------------------------------------

KNOWN ISSUES

- File Name Mismatch: If the downloaded file name differs from the expected name, the program logs a warning. It handles this by searching for files using original Spotify track and artist names.
- Rate Limiting: Excessive requests to the Spotify API or YouTube Music may cause temporary download failures.

------------------------------------------------------------

CONTRIBUTING

Contributions are welcome! Feel free to open issues or submit pull requests.

------------------------------------------------------------

LICENSE

This project is licensed under the MIT License. See the LICENSE file for details.

------------------------------------------------------------

ACKNOWLEDGMENTS

- Spotify API
- spotdl
- PyQt6
- FFmpeg
