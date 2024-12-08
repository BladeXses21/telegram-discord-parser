import os
import sys
import json
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit


def resource_path(relative_path):
    """Отримує абсолютний шлях до ресурсу, працює як у разі запуску скрипту, так і для згенерованого exe"""
    try:
        # PyInstaller створює тимчасову директорію і зберігає шлях у _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_config():
    with open(resource_path('config.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_data):
    with open(resource_path('config.json'), 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)


def clear_discord_messages():
    with open(resource_path('discord_messages.json'), 'w', encoding='utf-8') as f:
        json.dump({}, f)


class TGDiscordInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.discord_process = None
        self.telegram_process = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('TG Discord Interface')
        layout = QVBoxLayout()

        # Input fields for configurations
        self.api_id_input = QLineEdit(self)
        self.api_id_input.setText(self.config['account']['api_id'])
        layout.addWidget(QLabel('API ID:'))
        layout.addWidget(self.api_id_input)

        self.api_hash_input = QLineEdit(self)
        self.api_hash_input.setText(self.config['account']['api_hash'])
        layout.addWidget(QLabel('API Hash:'))
        layout.addWidget(self.api_hash_input)

        self.source_channel_input = QLineEdit(self)
        self.source_channel_input.setText(', '.join(map(str, self.config['source_channel_ids'])))
        layout.addWidget(QLabel('Source Channel IDs (comma separated):'))
        layout.addWidget(self.source_channel_input)

        self.destination_channel_input = QLineEdit(self)
        self.destination_channel_input.setText(', '.join(self.config['destination_channel_usernames']))
        layout.addWidget(QLabel('Destination Channels (comma separated):'))
        layout.addWidget(self.destination_channel_input)

        self.discord_token_input = QLineEdit(self)
        self.discord_token_input.setText(self.config['DISCORD_TOKEN'])
        layout.addWidget(QLabel('Discord Token:'))
        layout.addWidget(self.discord_token_input)

        self.guild_id_input = QLineEdit(self)
        self.guild_id_input.setText(self.config['TARGET_GUILD_ID'])
        layout.addWidget(QLabel('Target Guild ID:'))
        layout.addWidget(self.guild_id_input)

        # Apply button to save config
        self.apply_btn = QPushButton('Apply', self)
        self.apply_btn.clicked.connect(self.update_config)
        layout.addWidget(self.apply_btn)

        # Start and Stop buttons
        self.start_btn = QPushButton('Start', self)
        self.start_btn.clicked.connect(self.start_services)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('Stop', self)
        self.stop_btn.clicked.connect(self.stop_services)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        self.setLayout(layout)

    def update_config(self):
        # Update config dictionary with new values
        self.config['account']['api_id'] = self.api_id_input.text()
        self.config['account']['api_hash'] = self.api_hash_input.text()
        self.config['source_channel_ids'] = list(map(int, self.source_channel_input.text().split(',')))
        self.config['destination_channel_usernames'] = self.destination_channel_input.text().split(',')
        self.config['DISCORD_TOKEN'] = self.discord_token_input.text()
        self.config['TARGET_GUILD_ID'] = self.guild_id_input.text()

        # Save updated config to file
        save_config(self.config)

    def start_services(self):
        current_directory = os.path.abspath(os.path.dirname(__file__))
        discord_parser_path = os.path.join(current_directory, 'discord_parser.py')
        telegram_parser_path = os.path.join(current_directory, 'telegram_parser.py')

        if sys.platform == "win32":
            self.discord_process = subprocess.Popen(
                ['cmd', '/k', f'python {discord_parser_path}'], creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.telegram_process = subprocess.Popen(
                ['cmd', '/k', f'python {telegram_parser_path}'], creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # для Linux або macOS
            self.discord_process = subprocess.Popen(
                ['gnome-terminal', '--', 'python3', discord_parser_path]
            )
            self.telegram_process = subprocess.Popen(
                ['gnome-terminal', '--', 'python3', telegram_parser_path]
            )

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_services(self):
        if self.discord_process:
            self.discord_process.terminate()
            self.discord_process.wait()
            self.discord_process = None
        if self.telegram_process:
            self.telegram_process.terminate()
            self.telegram_process.wait()
            self.telegram_process = None

        # Очистити вміст файлу discord_messages.json
        clear_discord_messages()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TGDiscordInterface()
    ex.show()
    sys.exit(app.exec_())
