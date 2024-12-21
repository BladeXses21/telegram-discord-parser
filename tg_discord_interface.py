import os
import sys
import json
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QHBoxLayout, QToolTip, \
    QScrollArea, QFrame

from expiry_date import check_expiry_date


def resource_path(relative_path):
    """Отримує абсолютний шлях до ресурсу, працює як у разі запуску скрипту, так і для згенерованого exe"""
    try:
        # PyInstaller створює тимчасову директорію і зберігає шлях у _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


import importlib.util

pars_conf_path = resource_path('pars_conf.py')
spec = importlib.util.spec_from_file_location("pars_conf", pars_conf_path)
pars_conf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pars_conf)

# Доступ до змінних з pars_conf
account = pars_conf.account
source_channel_ids = pars_conf.source_channel_ids
destination_channel_usernames = pars_conf.destination_channel_usernames
json_file_path = pars_conf.json_file_path

channel_map = pars_conf.channel_map


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
    channel_mappings = {}
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.discord_process = None
        self.telegram_process = None

        # Оголошення всіх атрибутів класу
        self.input_fields = []  # Список динамічних пар полів
        self.fields_layout = None  # ініціалізація для layout полів
        self.scroll_area = None

        self.initUI()
        self.load_channels()  # Завантаження існуючих даних із файлу

    def load_channels(self):
        """
        Завантажує пари "ID → URL" із JSON файлу в `input_fields`.
        """
        try:
            with open(channel_map, 'r', encoding='utf-8') as f:
                data = json.load(f)  # Завантаження даних з файлу
                for channel_id, channel_url in data.items():
                    self.add_channel_field()  # Створюємо нові поля
                    id_input, link_input = self.input_fields[-1]  # Остання додана пара
                    id_input.setText(channel_id)  # Встановлюємо значення ID
                    link_input.setText(channel_url)  # Встановлюємо значення URL
        except FileNotFoundError:
            print("Файл channel_to_channel.json не знайдено. Нових полів не додано.")
        except json.JSONDecodeError:
            print("Помилка декодування JSON. Перевірте структуру файлу.")

    def add_channel_field(self):
        """
        Додає новий рядок для вводу пари "ID → URL каналу".
        """
        sub_layout = QHBoxLayout()

        id_input = QLineEdit(self)
        id_input.setPlaceholderText("ID каналу (Discord/Telegram)")
        link_input = QLineEdit(self)
        link_input.setPlaceholderText("Посилання або ID каналу призначення")

        self.input_fields.append((id_input, link_input))

        sub_layout.addWidget(id_input)
        sub_layout.addWidget(link_input)
        self.fields_layout.addLayout(sub_layout)

    def initUI(self):
        self.setWindowTitle('TG Discord Interface')
        layout = QVBoxLayout()

        # Функція для створення поля вводу з підказкою
        def add_input_field(label_text, input_field, tooltip_text):
            sub_layout = QHBoxLayout()
            label = QLabel(label_text)
            tooltip_label = QLabel(' (?)')
            tooltip_label.setStyleSheet("color: blue;")
            QToolTip.setFont(tooltip_label.font())
            tooltip_label.setToolTip(tooltip_text)
            sub_layout.addWidget(label)
            sub_layout.addWidget(input_field)
            sub_layout.addWidget(tooltip_label)
            layout.addLayout(sub_layout)

        # Створення і додавання полів вводу з підказками
        self.api_id_input = QLineEdit(self)
        self.api_id_input.setText(self.config['account']['api_id'])
        add_input_field("API ID:", self.api_id_input,
                        "Введіть ваш API ID для Telegram. Ви можете отримати його на сайті my.telegram.org.")

        self.api_hash_input = QLineEdit(self)
        self.api_hash_input.setText(self.config['account']['api_hash'])
        add_input_field("API Hash:", self.api_hash_input,
                        "Введіть ваш API Hash для Telegram. Ви можете отримати його на сайті my.telegram.org.")

        self.source_channel_input = QLineEdit(self)
        self.source_channel_input.setText(', '.join(map(str, self.config['source_channel_ids'])))
        add_input_field("Source Channel IDs:", self.source_channel_input,
                        "Введіть ID каналу. Це ID можна отримати зайшовши в web версію телеграм, та обравши потрібний канал.\nПісля чого в строці адресу сторінки скопіювати id каналу")

        self.destination_channel_input = QLineEdit(self)
        self.destination_channel_input.setText(', '.join(self.config['destination_channel_usernames']))
        add_input_field("Destination Channels:", self.destination_channel_input,
                        "Введіть імена каналу. Наприклад, @channel_name або посилання наприклад, https://t.me/...")

        self.discord_token_input = QLineEdit(self)
        self.discord_token_input.setText(self.config['DISCORD_TOKEN'])
        add_input_field("Discord Token:", self.discord_token_input,
                        "Введіть ваш токен Discord. Його можна отримати у браузері скористайтеся клавішею F12, щоб викликати інструменти розробника. Якщо мова йде про клієнт Discord, то комбінація виглядає як Ctrl + Shift + I.\n"
                        "У цьому вікні перейдіть на вкладку «Network».\n"
                        "Напишіть будь-яке повідмолення у будь-який канал в discord.\n"
                        "Після цього у консолі розробника в активності з`явиться новий елемент message.\n"
                        "Нажміть на цей елемент та відкрийте в ньому вкладку Headers.\n"
                        "В ньому потрібно знайти назву Authorization - це і є Ваш TOKEN. (не передавайте його нікому)")


        # Нове поле для TARGET_GUILD_ID
        self.guild_id_input = QLineEdit(self)
        self.guild_id_input.setText(self.config.get('TARGET_GUILD_ID', ''))
        add_input_field("Target Guild ID:", self.guild_id_input,
                        "Введіть ID сервера Discord. Це можна отримати, увімкнувши 'Developer Mode' у Discord.")

        # Apply button to save config
        self.apply_btn_config = QPushButton('Apply config', self)
        self.apply_btn_config.clicked.connect(self.update_config)
        layout.addWidget(self.apply_btn_config)

        # Start and Stop buttons
        self.start_btn = QPushButton('Start', self)
        self.start_btn.clicked.connect(self.start_services)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton('Stop', self)
        self.stop_btn.clicked.connect(self.stop_services)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # Прокручувана область для полів пар каналів
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        self.fields_frame = QFrame()
        self.fields_layout = QVBoxLayout(self.fields_frame)

        # Додаємо перше поле
        self.add_channel_field()

        self.scroll_area.setWidget(self.fields_frame)
        layout.addWidget(self.scroll_area)

        # Кнопка "+" для нових пар
        self.add_btn = QPushButton('+', self)
        self.add_btn.clicked.connect(self.add_channel_field)
        layout.addWidget(self.add_btn)

        # Кнопка "Apply" для збереження
        self.apply_btn_channels = QPushButton('Apply channels', self)
        self.apply_btn_channels.clicked.connect(self.save_channels)
        layout.addWidget(self.apply_btn_channels)

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
        print("Конфігурація успішно оновлена.")

    def start_services(self):
        current_directory = os.path.abspath(os.path.dirname(__file__))
        discord_parser_path = os.path.join(current_directory, 'discord_parser.py')
        telegram_parser_path = os.path.join(current_directory, 'telegram_parser.py')

        if sys.platform == "win32":
            # Запускаємо процеси напряму без використання `cmd.exe`
            self.discord_process = subprocess.Popen(
                ['python', discord_parser_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.telegram_process = subprocess.Popen(
                ['python', telegram_parser_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Для Linux/macOS залишаємо стандартний запуск
            self.discord_process = subprocess.Popen(
                ['python3', discord_parser_path]
            )
            self.telegram_process = subprocess.Popen(
                ['python3', telegram_parser_path]
            )

        # Зберігаємо PID процесів у змінну
        self.discord_pid = self.discord_process.pid
        self.telegram_pid = self.telegram_process.pid

        print(f"Discord процес запущено з PID: {self.discord_pid}")
        print(f"Telegram процес запущено з PID: {self.telegram_pid}")

        # Деактивація кнопки Start після запуску
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_services(self):
        # Перевірка й завершення Discord процесу
        if self.discord_process:
            try:
                self.discord_process.terminate()  # Завершення процесу через terminate()
                self.discord_process.wait()  # Очікуємо закриття
                print(f"Discord процес з PID {self.discord_pid} зупинено.")
            except Exception as e:
                print(f"Помилка під час завершення Discord: {e}")
            self.discord_process = None

        # Перевірка й завершення Telegram процесу
        if self.telegram_process:
            try:
                self.telegram_process.terminate()  # Завершення процесу через terminate()
                self.telegram_process.wait()  # Очікуємо закриття
                print(f"Telegram процес з PID {self.telegram_pid} зупинено.")
            except Exception as e:
                print(f"Помилка під час завершення Telegram: {e}")
            self.telegram_process = None

        # Очистити файл Discord повідомлень
        clear_discord_messages()

        # Увімкнути кнопку "Start" і вимкнути кнопку "Stop"
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def save_channels(self):
        """
        Метод отримує всі пари "ID → URL", введені у динамічних полях, і зберігає їх у файл `channel_to_channel.json`.
        """
        self.channel_mappings = {}  # Очищуємо попередній словник

        # Перебираємо всі пари полів введення
        for id_input, link_input in self.input_fields:
            channel_id = id_input.text().strip()  # Зчитуємо текст з поля ID
            channel_url = link_input.text().strip()  # Зчитуємо текст з поля URL

            # Додавання лише непустих значень
            if channel_id and channel_url:
                self.channel_mappings[channel_id] = channel_url

        # Якщо є дані, зберігаємо їх в JSON файл
        if self.channel_mappings:  # Перевіряємо, чи є значення у словнику
            with open('channel_to_channel.json', 'w', encoding='utf-8') as f:
                json.dump(self.channel_mappings, f, ensure_ascii=False, indent=4)
            print("Збережено до channel_to_channel.json:", self.channel_mappings)
        else:
            print("Помилка: Дані для збереження відсутні.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TGDiscordInterface()

    check_expiry_date(ex)

    ex.show()
    sys.exit(app.exec_())
