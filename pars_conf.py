import os
import sys
import json


# Забезпечує правильний шлях до файлу
def resource_path(relative_path):
    """Отримує шлях до ресурсу, враховуючи PyInstaller (_MEIPASS)."""
    try:
        # Якщо виконується в режимі .exe
        base_path = sys._MEIPASS
    except AttributeError:
        # Якщо виконується як скрипт
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Використовуємо resource_path для пошуку config.json
config_path = resource_path('config.json')

# Завантажуємо config.json
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError as e:
    # Покажемо зрозуміле повідомлення помилки, якщо файл не знайдено
    print(f"Помилка: Файл config.json не знайдено за шляхом: {config_path}")
    raise FileNotFoundError(f"Файл config.json не знайдено: {config_path}") from e

# Експортуємо змінні із config.json
account = config['account']
source_channel_ids = config['source_channel_ids']
destination_channel_usernames = config['destination_channel_usernames']

DISCORD_TOKEN = config['DISCORD_TOKEN']  # Discord API токен
TARGET_GUILD_ID = config['TARGET_GUILD_ID']  # ID цільового каналу

json_file_path = resource_path('discord_messages.json')  # Окремий файл

channel_map = resource_path('channel_to_channel.json')