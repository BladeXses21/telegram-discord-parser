import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from pars_conf import account, source_channel_ids, destination_channel_usernames


class TGDiscordInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.discord_process = None
        self.telegram_process = None

    def initUI(self):
        self.setWindowTitle('TG Discord Interface')

        layout = QVBoxLayout()

        # Display API ID and API Hash
        self.api_id_label = QLabel(f"API ID: {account['api_id']}", self)
        self.api_hash_label = QLabel(f"API Hash: {account['api_hash']}", self)

        layout.addWidget(self.api_id_label)
        layout.addWidget(self.api_hash_label)

        # Display other configuration details
        self.config_label = QLabel(f"Source Channel IDs: {source_channel_ids}", self)
        layout.addWidget(self.config_label)
        self.dest_label = QLabel(f"Destination Channels: {destination_channel_usernames}", self)
        layout.addWidget(self.dest_label)

        # Start and Stop buttons
        self.start_btn = QPushButton('Start', self)
        self.start_btn.clicked.connect(self.start_services)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('Stop', self)
        self.stop_btn.clicked.connect(self.stop_services)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)

    def start_services(self):
        if not self.discord_process:
            self.discord_process = subprocess.Popen(
                ['python', 'discord_parser.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("Discord script started")

        if not self.telegram_process:
            self.telegram_process = subprocess.Popen(
                ['python', 'telegram_parser.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("Telegram script started")

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_services(self):
        if self.discord_process:
            self.discord_process.terminate()
            self.discord_process = None
            print("Discord script stopped")

        if self.telegram_process:
            self.telegram_process.terminate()
            self.telegram_process = None
            print("Telegram script stopped")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TGDiscordInterface()
    ex.show()
    sys.exit(app.exec_())
