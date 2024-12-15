import asyncio
import os
import json

from telethon import TelegramClient, events
from pars_conf import account, source_channel_ids, destination_channel_usernames, json_file_path
from telethon.tl.types import User, Channel, Chat


class TelegramBot:
    def __init__(self, api_id, api_hash):
        self.client = TelegramClient('msgPars', api_id, api_hash)
        self.last_modified_time = 0
        self.cached_channels = {}

    async def forward_message(self, message, files=None, reply_to=None):
        """
        Send message and/or reply to Telegram channel.
        Args:
            message: Основний текст повідомлення.
            files: Список файлів для пересилання.
            reply_to: Інформація про відповідь (dict), якщо є.
                dict має ключі "author" і "content".
        """
        for destination in destination_channel_usernames:
            try:
                if destination not in self.cached_channels:
                    if destination.startswith('https://t.me/'):
                        self.cached_channels[destination] = await self.client.get_entity(destination)
                    elif destination.startswith('@'):
                        self.cached_channels[destination] = await self.client.get_entity(destination)
                    elif destination.isdigit() or destination.startswith("-100"):
                        channel_id = int(destination) if destination.startswith("-100") else int(f"-100{destination}")
                        self.cached_channels[destination] = channel_id
                    else:
                        raise ValueError(f"Invalid destination: {destination}")

                channel = self.cached_channels[destination]

                # Очікуємо та формуємо текст, включаючи інформацію про відповдіь, якщо є
                if reply_to:
                    reply_text = (
                        f'Відповідь на: {reply_to["author"]}\n`{reply_to["content"]}`\n\n'
                    )
                else:
                    reply_text = ""

                full_message = f"{reply_text}{message}"

                if files:
                    files_to_remove = []  # Очікуємо на успішну передачу файлів

                    for file in files:
                        try:
                            # Якщо є і текст, і файл, відправляємо їх разом.
                            await self.client.send_file(channel, file, caption=full_message or "")
                            files_to_remove.append(file)
                            print(f"Файл {file} успішно відправлено.")
                        except Exception as e:
                            print(f"Error sending file: {file}: {e}")

                    for file in files_to_remove:
                        try:
                            os.remove(file)
                            print(f'Файл {file} був успішно видалено.')
                        except Exception as e:
                            print(f'Error while deleting file {file}: {e}.')
                    # Лог файлів, які не видалені
                    for file in set(files) - set(files_to_remove):
                        print(f"The file {file} was not sent and remained on disk.")

                # Якщо є тільки текст (без файлів), відправляємо його як окреме повідомлення
                elif full_message:
                    await self.client.send_message(channel, full_message)

                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to send message to {destination}: {e}")

    def setup_message_handler(self):
        @self.client.on(events.NewMessage(chats=source_channel_ids))
        async def handle_event(event):
            try:
                if event.message.sender:
                    sender = event.message.sender
                    if isinstance(sender, User):  # Якщо це індивідуальний користувач
                        author_name = sender.username or sender.first_name or sender.last_name or ""
                    elif isinstance(sender, (Channel, Chat)):  # Якщо це канал або група
                        author_name = sender.title or ""
                    else:
                        author_name = ""
                else:
                    author_name = ""

                # Формування тексту повідомлення
                message = f"`{author_name}:`\n{event.message.message}"  # Текст повідомлення

                media = event.message.media  # Фотографії, файли, тощо
                reply_to_msg_id = event.message.reply_to_msg_id  # ID повідомлення, на яке посилаються
                files = [] # Список файлів для пересилання
                reply_to = None  # Дані про відповідь

                # Якщо є медіафайли, завантажуємо їх для пересилання
                if media:
                    file_name = await self.client.download_media(media)
                    if file_name:
                        files.append(file_name)
                        print(f"Медіа {file_name} завантажено для пересилання.")

                # Якщо повідомлення є відповіддю, отримуємо текст і автора оригінального повідомлення
                if reply_to_msg_id:
                    original_message = await event.message.get_reply_message()
                    if original_message:
                        if original_message.sender:
                            sender = original_message.sender
                            if isinstance(sender, User):
                                # Якщо це індивідуальний користувач із username
                                reply_author = sender.username or sender.first_name or sender.last_name or ""
                            elif isinstance(sender, (Channel, Chat)):
                                # Якщо це канал або група
                                reply_author = sender.title or ""
                            else:
                                # Якщо це індивідуальний користувач без username
                                reply_author = ""
                        else:
                            reply_author = ""

                        reply_to = {
                            "author": reply_author,
                            "content": original_message.message or ""
                        }
                        print(f"Відповідає на повідомлення від {reply_to['author']}: {reply_to['content']}")

                # Відправляємо всі отримані дані далі
                await self.forward_message(message, files=files, reply_to=reply_to)
            except Exception as e:
                print(f"Помилка під час обробки повідомлення: {e}")

    async def watch_file(self):
        processed_messages = set()

        while True:
            await asyncio.sleep(1)

            try:
                current_modified_time = os.path.getmtime(json_file_path)
                if current_modified_time != self.last_modified_time:
                    self.last_modified_time = current_modified_time

                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # create unique key for message (hash)
                    content = data.get('content', '')
                    author = data.get('author', '')
                    files = data.get('files', [])
                    reply_to = data.get('referenced_message', None)  # Перевірка інформації про відповідь

                    # Формуємо текст повідомлення
                    message = f"`{author}:`\n{content}"
                    # Перевірка унікальності повідомлення
                    message_hash = hash((message, tuple(files), json.dumps(reply_to, sort_keys=True)))

                    if message_hash not in processed_messages:
                        await self.forward_message(message, files=files, reply_to=reply_to)
                        processed_messages.add(message_hash)  # add unique key to list

                    else:
                        print("Message already processed. Skipping...")

            except Exception as e:
                print(f"Помилка зчитування файлу або надсилання повідомлення: {e}")

    async def start(self):
        await self.client.start()
        print('Telegram client started and watching file for changes...')
        self.setup_message_handler()

        await self.watch_file()

        await self.client.run_until_disconnected()


async def main():
    telegram_bot = TelegramBot(account['api_id'], account['api_hash'])
    await telegram_bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Зупинка через Ctrl+C.")
    finally:
        print("Telegram-парсер завершив роботу.")
