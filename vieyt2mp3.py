import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QProgressBar, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from yt_dlp import YoutubeDL
from pathlib import Path


class DownloaderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, download_path):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.latest_filepath = None

    def run(self):
        def progress_hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0.0%').strip().replace('%', '')
                try:
                    self.progress.emit(int(float(percent)))
                except ValueError:
                    pass
            elif d['status'] == 'finished':
                self.latest_filepath = d['filename']

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [progress_hook],
            'ffmpeg_location': os.path.join(os.path.dirname(sys.executable), 'ffmpeg', 'bin')
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.finished.emit(True, self.latest_filepath)
        except Exception as e:
            self.finished.emit(False, str(e))


class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube to MP3 Downloader")
        self.setFixedSize(500, 250)
        self.setup_ui()
        self.downloader_thread = None

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.label = QLabel("Paste YouTube URL:")
        self.label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setStyleSheet("padding: 6px; font-size: 14px;")
        layout.addWidget(self.url_input)

        self.download_button = QPushButton("Download as MP3")
        self.download_button.setStyleSheet("padding: 8px; font-size: 14px; background-color: #4CAF50; color: white;")
        self.download_button.clicked.connect(self.download)
        layout.addWidget(self.download_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("height: 20px;")
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 13px; color: #333;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def download(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("Please enter a YouTube URL.")
            return

        downloads_folder = str(Path.home() / "Downloads")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.download_button.setEnabled(False)
        self.status_label.setText("Starting download...")

        self.downloader_thread = DownloaderThread(url, downloads_folder)
        self.downloader_thread.progress.connect(self.progress_bar.setValue)
        self.downloader_thread.finished.connect(self.on_download_finished)
        self.downloader_thread.start()

    def on_download_finished(self, success, info):
        self.download_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            mp3_path = os.path.splitext(info)[0] + '.mp3'
            self.status_label.setText("Download completed!")
            if os.path.exists(mp3_path):
                subprocess.run(f'explorer /select,"{mp3_path}"')
            else:
                subprocess.run(f'explorer "{os.path.dirname(info)}"')
        else:
            self.status_label.setText(f"Download failed: {info}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())
