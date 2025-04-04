from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QProgressBar, QFileDialog, QLineEdit, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from downloader import DownloadThread


class SpotifyDownloaderGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.download_folder = ""
        self.download_thread = None  # Initialize download thread
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Spotify Playlist Downloader")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        # Playlist URL Input
        self.playlist_input = self.create_playlist_input()
        layout.addWidget(self.playlist_input)

        # Folder Selection Button
        self.folder_button = self.create_folder_button()
        layout.addWidget(self.folder_button)

        # Quality Dropdown
        self.quality_dropdown = self.create_quality_dropdown()
        layout.addWidget(self.quality_dropdown)

        # Status Label
        self.status_label = self.create_status_label()
        layout.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = self.create_progress_bar()
        layout.addWidget(self.progress_bar)

        # Start Button
        self.start_button = self.create_start_button()
        layout.addWidget(self.start_button)

        # Cancel Button
        self.cancel_button = self.create_cancel_button()
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def create_playlist_input(self):
        """Create the playlist URL input field."""
        playlist_input = QLineEdit(self)
        playlist_input.setPlaceholderText("Enter Spotify Playlist URL")
        return playlist_input

    def create_folder_button(self):
        """Create the folder selection button."""
        folder_button = QPushButton("Select Download Folder", self)
        folder_button.clicked.connect(self.select_folder)
        return folder_button

    def create_quality_dropdown(self):
        """Create the quality selection dropdown."""
        quality_dropdown = QComboBox(self)
        quality_dropdown.addItems(["128k", "192k", "256k", "320k"])
        return quality_dropdown

    def create_status_label(self):
        """Create the status label."""
        status_label = QLabel("Status: Waiting for input...", self)
        return status_label

    def create_progress_bar(self):
        """Create the progress bar."""
        progress_bar = QProgressBar(self)
        progress_bar.setValue(0)
        return progress_bar

    def create_start_button(self):
        """Create the start download button."""
        start_button = QPushButton("Start Download", self)
        start_button.clicked.connect(self.start_download)
        return start_button

    def create_cancel_button(self):
        """Create the cancel download button."""
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.cancel_download)
        cancel_button.setEnabled(False)
        return cancel_button

    def select_folder(self):
        """Open a dialog to select the download folder."""
        self.download_folder = QFileDialog.getExistingDirectory(self, "Select Folder")

    def start_download(self):
        """Start the download process."""
        playlist_url = self.playlist_input.text().strip()
        quality = self.quality_dropdown.currentText()

        if not self.download_folder or not playlist_url:
            self.status_label.setText("❌ Please select folder and enter playlist URL")
            return

        self.initialize_download_thread(playlist_url, quality)

    def initialize_download_thread(self, playlist_url, quality):
        """Initialize and start the download thread."""
        self.download_thread = DownloadThread(playlist_url, self.download_folder, quality)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.status_signal.connect(self.status_label.setText)
        self.download_thread.finished.connect(self.download_finished)

        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.download_thread.start()

    def cancel_download(self):
        """Cancel the ongoing download."""
        if self.download_thread:
            self.download_thread.cancel()
            self.status_label.setText("❌ Download Cancelled")

    def download_finished(self):
        """Handle the completion of the download."""
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)


if __name__ == "__main__":
    app = QApplication([])
    window = SpotifyDownloaderGUI()
    window.show()
    app.exec()