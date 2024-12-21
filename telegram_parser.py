import asyncio
import os
import json

from telethon import TelegramClient, events
from pars_conf import account, source_channel_ids, destination_channel_usernames, json_file_path, channel_map
from telethon.tl.types import User, Channel, Chat
from telethon.tl.functions.channels import CreateChannelRequest


class TelegramBot:
    def __init__(self, api_id, api_hash):
        self.client = TelegramClient('msgPars', api_id, api_hash)
        self.last_modified_time = 0
        self.cached_channels = {}

    async def forward_message(self, message, files=None, reply_to=None, target_chanel=None):
        """
        Оновлений код для обробки формату повідомлень.
        Args:
            message: Основний текст повідомлення.
            files: Список файлів для пересилання.
            reply_to: Інформація про відповідь (dict), якщо є (з полями "branch_name", "author", "content").
            target_chanel: Канал, у який слід переслати повідомлення, прив'язка каналів з файлу channel_to_channel.json.
        """
        try:
            # Якщо задано цільовий канал, перевіряємо/підключаємо його
            if target_chanel:
                if target_chanel not in self.cached_channels:
                    if target_chanel.startswith('https://t.me/'):
                        self.cached_channels[target_chanel] = await self.client.get_entity(target_chanel)
                    elif target_chanel.startswith('@'):
                        self.cached_channels[target_chanel] = await self.client.get_entity(target_chanel)
                    elif target_chanel.isdigit() or target_chanel.startswith("-100"):
                        channel_id = int(target_chanel) if target_chanel.startswith("-100") else int(
                            f"-100{target_chanel}")
                        self.cached_channels[target_chanel] = channel_id
                    else:
                        raise ValueError(f"Invalid destination: {target_chanel}")

                channel = self.cached_channels[target_chanel]

                # Формування тексту повідомлення
                if reply_to:
                    if "branch_name" in reply_to and reply_to["branch_name"]:  # Відповідь у Telegram-гілці
                        reply_text = (
                            f'автор `{reply_to["author"]}`" '
                            f'{reply_to["content"]}\n\n'
                        )
                    else:  # Відповідь у іншій платформі
                        reply_text = (
                            f'Відповідь на повідомлення `{reply_to["author"]}`\n'
                            f'{reply_to["content"]}\n\n'
                        )
                else:
                    reply_text = ""

                full_message = f"{reply_text}{message}"

                # Відправлення файлів із повідомленням
                if files:
                    files_to_remove = []

                    for file in files:
                        try:
                            await self.client.send_file(channel, file, caption=full_message or "")
                            files_to_remove.append(file)
                            print(f"Файл {file} успішно відправлено.")
                        except Exception as e:
                            print(f"Помилка при відправленні файлу {file}: {e}")

                    # Видалення файлів після успішної відправки
                    for file in files_to_remove:
                        try:
                            os.remove(file)
                            print(f'Файл {file} успішно видалено.')
                        except Exception as e:
                            print(f'Помилка при видаленні файлу {file}: {e}.')

                elif full_message:  # Якщо тільки текст
                    await self.client.send_message(channel, full_message)

                await asyncio.sleep(1)

        except Exception as e:
            print(f"Помилка при пересиланні повідомлення в {target_chanel}: {e}")

    def setup_message_handler(self):
        @self.client.on(events.NewMessage(chats=source_channel_ids))
        async def handle_event(event):
            try:
                # Зчитування каналу-отримувача з файлу channel_to_channel.json
                with open(channel_map, 'r', encoding='utf-8') as f:
                    required_channels = json.load(f)

                # ID основної групи (завжди) і гілки (якщо є)
                source_channel_id = str(event.chat_id)

                # Перевіряємо, якщо це гілка (форум)
                if event.message.reply_to_msg_id:
                    thread_id = event.message.reply_to_msg_id  # Унікальний ID для гілки
                    source_channel_id = f"{source_channel_id}_{thread_id}"  # Формуємо нове ID для гілки

                # Логування для налагодження
                print(f"Обробляється повідомлення: ID групи/гілки - {source_channel_id}")

                # Перевіряємо, чи є ID каналу/гілки в JSON
                if source_channel_id not in required_channels:
                    print(f"Channel {source_channel_id} not found in channel_to_channel.json. Skipping...")
                    return

                # Отримаємо кінцевий канал куди потрібно переслати повідомлення
                target_channel = required_channels[source_channel_id]
                print(f"Пересилається до каналу: {target_channel}")

                author_name = ""
                branch_name = None
                if event.message.sender:
                    sender = event.message.sender
                    if isinstance(sender, User):  # Якщо це користувач
                        author_name = sender.username or sender.first_name or sender.last_name or ""
                    elif isinstance(sender, (Channel, Chat)):  # Якщо це канал або група
                        author_name = sender.title or ""
                    else:
                        author_name = ""

                if event.chat and event.chat.title:
                    branch_name = event.chat.title

                message_content = event.message.message  # Основний текст повідомлення
                reply_to_msg_id = event.message.reply_to_msg_id  # ID відповіді
                files = []
                reply_to = None

                # Якщо є файли, завантажуємо їх
                if event.message.media:
                    file_name = await self.client.download_media(event.message.media)
                    if file_name:
                        files.append(file_name)

                # Якщо є відповідь
                if reply_to_msg_id:
                    original_message = await event.message.get_reply_message()
                    if original_message:
                        original_author_name = ""
                        if original_message.sender:
                            sender = original_message.sender
                            if isinstance(sender, User):
                                original_author_name = sender.username or sender.first_name or sender.last_name or ""
                            elif isinstance(sender, (Channel, Chat)):
                                original_author_name = sender.title or ""

                        reply_to = {
                            "branch_name": branch_name,
                            "author": original_author_name,
                            "content": original_message.message or ""
                        }

                full_message = f'`{branch_name} {author_name}:`\n{message_content}' if branch_name else f'`{author_name}:`\n{message_content}'

                await self.forward_message(full_message, files=files, reply_to=reply_to, target_chanel=target_channel)

            except Exception as e:
                print(f"Помилка обробки повідомлення: {e}")

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

                    # Зчитування каналу-отримувача з файлу channel_to_channel.json
                    with open(channel_map, 'r', encoding='utf-8') as f:
                        required_channels = json.load(f)

                    # create unique key for message (hash)
                    channel_id = data.get('channel_id', '')
                    content = data.get('content', '')
                    author = data.get('author', '')
                    files = data.get('files', [])
                    reply_to = data.get('referenced_message', None)  # Перевірка інформації про відповідь

                    # Формуємо текст повідомлення
                    message = f"`{author}:`\n{content}"
                    # Перевірка унікальності повідомлення
                    message_hash = hash((message, tuple(files), json.dumps(reply_to, sort_keys=True)))

                    # Перевіряємо, чи є ID каналу discord в JSON
                    if channel_id not in required_channels:
                        print(f"Discord Channel {channel_id} not found in channel_to_channel.json. Skipping...")

                    target_channel = required_channels[channel_id]

                    if message_hash not in processed_messages:
                        await self.forward_message(message, files=files, reply_to=reply_to, target_chanel=target_channel)
                        processed_messages.add(message_hash)  # add unique key to list

                    else:
                        print("Message already processed. Skipping...")

            except Exception as e:
                print(f"Помилка зчитування файлу або надсилання повідомлення: {e}")


    async def start(self):
        await self.client.start()
        print('Telegram client started and watching file for changes...')

        # await self.get_threads_in_supergroup(source_channel_ids)

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
