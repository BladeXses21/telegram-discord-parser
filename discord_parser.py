import asyncio
import json
import os
import time
from typing import List, Optional

import requests
from pars_conf import DISCORD_TOKEN, json_file_path, TARGET_GUILD_ID

headers = {
    "Authorization": DISCORD_TOKEN,
    "Content-Type": "application/json",
}

guild_channels_url = f"https://discord.com/api/v10/guilds/{TARGET_GUILD_ID}/channels"

last_saved_ids = {}


async def get_all_channels() -> List[dict]:
    """
    Отримує всі текстові канали в гільдії.
    """
    response = requests.get(guild_channels_url, headers=headers)
    if response.status_code == 200:
        try:
            channels = response.json()
            # Фільтруємо текстові канали
            text_channels = [channel for channel in channels if channel["type"] == 0]
            return text_channels
        except json.JSONDecodeError:
            print("Не вдалося декодувати JSON при отриманні списку каналів.")
    else:
        print(f"Помилка: не вдалося отримати канали (HTTP {response.status_code}).")
    return []


async def get_last_message_from_channel(channel_id: str):
    """
    Отримує останнє повідомлення з конкретного каналу із врахуванням referenced_message
    та додає затримку між обробкою повідомлень.
    """
    global last_saved_ids

    channel_messages_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    params = {"limit": 1}  # Отримуємо лише останнє повідомлення
    response = requests.get(channel_messages_url, headers=headers, params=params)

    if response.status_code == 200:
        try:
            messages = response.json()
            if messages:
                message = messages[0]
                message_id = message["id"]  # Унікальний ідентифікатор повідомлення
                message_content = message["content"]
                message_author = message["author"]["username"]  # Автор повідомлення
                attachments = message.get("attachments", [])
                referenced_message = message.get("referenced_message", None)  # Додаємо перевірку `referenced_message`

                # Перевірка, чи це повідомлення вже оброблено
                if last_saved_ids.get(channel_id) == message_id:
                    print(f"Канал {channel_id}: Повідомлення вже оброблено. Пропускаю...")
                    return

                # Оновлюємо останній оброблений ідентифікатор
                last_saved_ids[channel_id] = message_id

                # Інформація про відповіді, якщо є referenced_message
                ref_author = None
                ref_content = None
                if referenced_message:
                    ref_author = referenced_message["author"]["username"]
                    ref_content = referenced_message["content"]
                    print(f"Канал {channel_id}: Повідомлення посилається на {ref_author}: {ref_content}")

                # Обробляємо вкладення
                files = []
                for attachment in attachments:
                    file_url = attachment["url"]
                    file_name = attachment["filename"]

                    file_content = requests.get(file_url, headers=headers)
                    if file_content.status_code == 200:
                        with open(file_name, "wb") as file:
                            file.write(file_content.content)
                        print(f"Канал {channel_id}: Завантажено файл: {file_name}")
                        files.append(file_name)
                    else:
                        print(f"Не вдалося завантажити файл {file_name} з каналу {channel_id}")

                # Формуємо дані для збереження в JSON
                data = {
                    "channel_id": channel_id,
                    "author": message_author,
                    "content": message_content,
                    "files": files,
                }

                # Додаємо інформацію про referenced_message, якщо вона існує
                if ref_author and ref_content:
                    data["referenced_message"] = {
                        "author": ref_author,
                        "content": ref_content,
                    }

                # Зберігаємо повідомлення в JSON
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                print(f"Канал {channel_id}: Нове повідомлення від {message_author}: {message_content}")

                # Затримка у 5 секунд перед обробкою наступного повідомлення
                await asyncio.sleep(1)

            else:
                print(f"Канал {channel_id}: У каналі немає нових повідомлень.")
        except requests.exceptions.JSONDecodeError:
            print(f"Канал {channel_id}: Не вдалося декодувати JSON. Сирий відповідь:", response.text)
    elif response.status_code in {403, 404, 401, 429}:
        print(f"Канал {channel_id}: Статус {response.status_code}. Додаткова інформація: {response.text}")
    else:
        print(f"Канал {channel_id}: Неочікувана помилка: {response.status_code} - {response.text}")


async def monitor_channels():
    """
    Основний асинхронний процес для моніторингу всіх каналів з урахуванням затримки між повідомленнями.
    """
    while True:
        try:
            print("Отримую список каналів...")
            channels = await get_all_channels()

            if not channels:
                print("Не вдалося знайти текстові канали або відсутній доступ.")
                continue

            # Проходимо по кожному текстовому каналу
            for channel in channels:
                channel_id = channel["id"]
                await get_last_message_from_channel(channel_id)

            # Затримка на 30 секунд між обробкою списку каналів
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Помилка в моніторингу каналів: {e}")



if __name__ == "__main__":
    try:
        asyncio.run(monitor_channels())
    except KeyboardInterrupt:
        print("Зупинка через Ctrl+C.")
    finally:
        print("Парсер Discord завершив роботу.")



