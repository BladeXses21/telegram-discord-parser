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
                await asyncio.sleep(5)

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
            await asyncio.sleep(30)

        except Exception as e:
            print(f"Помилка в моніторингу каналів: {e}")



if __name__ == "__main__":
    try:
        asyncio.run(monitor_channels())
    except KeyboardInterrupt:
        print("Зупинка через Ctrl+C.")
    finally:
        print("Парсер Discord завершив роботу.")



# import asyncio
# import json
# import os
# import time
#
# import requests
# from pars_conf import DISCORD_TOKEN, json_file_path, TARGET_GUILD_ID
#
#
# headers = {
#     "Authorization": DISCORD_TOKEN,
#     "Content-Type": "application/json",
# }
#
# url = f"https://discord.com/api/v10/guilds/{TARGET_GUILD_ID}/channels"
#
# last_saved_id = None
#
# def get_last_message():
#     global last_saved_id
#     response = requests.get(url, headers=headers, params={"limit": 1})
#
#     if response.status_code == 200:
#         try:
#             messages = response.json()
#             if messages:
#                 message = messages[0]
#                 message_id = message['id']  # Унікальний ідентифікатор повідомлення
#                 message_content = message['content']
#                 message_author = message['author']['username']  # Автор повідомлення
#                 attachments = message.get('attachments', [])
#                 referenced_message = message.get(
#                     'referenced_message')  # Перевіряємо, чи є посилання на інше повідомлення
#
#                 # Перевіряємо, чи вже це повідомлення оброблено
#                 if message_id == last_saved_id:
#                     print("Повідомлення вже оброблено. Пропускаю...")
#                     return
#
#                 # Зберігаємо ідентифікатор як останній оброблений
#                 last_saved_id = message_id
#
#                 # Інформація про відповідь/переслане повідомлення
#                 ref_author = None
#                 ref_content = None
#                 thread_name = None
#
#                 if referenced_message:
#                     ref_author = referenced_message['author']['username']  # Автор оригінального повідомлення
#                     ref_content = referenced_message['content']  # Текст оригінального повідомлення
#
#                     # Якщо посилання пов'язане з гілкою, беремо її назву
#                     if 'thread' in referenced_message:
#                         thread_name = referenced_message['thread']['name']
#
#                     print(f"Переслано повідомлення від {ref_author} з гілки: {thread_name or 'Без назви'}")
#                     print(f"Повідомлення з гілки: {ref_content}")
#
#                 # Виведення основного повідомлення
#                 print(f"{message_author} сказав: {message_content}")
#
#                 files = []
#                 for attachment in attachments:
#                     file_url = attachment['url']
#                     file_name = attachment['filename']
#
#                     file_content = requests.get(file_url, headers=headers)
#                     if file_content.status_code == 200:
#                         with open(file_name, 'wb') as file:
#                             file.write(file_content.content)
#                         print(f'Завантажено файл: {file_name}')
#                         files.append(file_name)  # Зберігаємо шлях до локального файлу
#                     else:
#                         print(f"Не вдалося завантажити файл {file_name}")
#
#                 # Формуємо дані для збереження в JSON
#                 data = {
#                     'author': message_author,
#                     'content': message_content,
#                     'files': files,
#                 }
#
#                 # Додаємо дані про відповідь, якщо вона є
#                 if ref_author and ref_content:
#                     data['forwarded_message'] = {
#                         'author': ref_author,
#                         'content': ref_content,
#                         'thread': thread_name or None
#                     }
#
#                 # Зберігаємо нове повідомлення в JSON
#                 with open(json_file_path, 'w', encoding='utf-8') as f:
#                     json.dump(data, f, ensure_ascii=False, indent=4)
#
#             else:
#                 print("У каналі немає нових повідомлень.")
#         except requests.exceptions.JSONDecodeError:
#             print("Не вдалося декодувати JSON. Сирий відповідь:", response.text)
#     elif response.status_code == 403:
#         print("Bot lacks permissions to access the specified channel (403 Forbidden).")
#     elif response.status_code == 404:
#         print("Channel not found (404 Not Found). Check your CHANNEL_ID.")
#     elif response.status_code == 401:
#         print("Authentication failed (401 Unauthorized). Check your bot token.")
#     elif response.status_code == 429:
#         print("Rate limit exceeded (429 Too Many Requests).")
#         print("Response headers:", response.headers)
#     else:
#         print(f"Unexpected error: {response.status_code} - {response.text}")
#
#
#
#
#
#
# if __name__ == "__main__":
#     try:
#         while True:
#             get_last_message()
#             time.sleep(1)
#     except KeyboardInterrupt:
#         print("Зупинка через Ctrl+C.")
#     finally:
#         print("Парсер Discord завершив роботу.")
#
