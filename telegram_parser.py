import asyncio
import os
import json
from telethon import TelegramClient, events
from pars_conf import account, source_channel_ids, destination_channel_usernames, json_file_path


class TelegramBot:
    def __init__(self, api_id, api_hash):
        self.client = TelegramClient('msgPars', api_id, api_hash)
        self.last_modified_time = 0

    async def forward_message(self, message, media=None):
        for destination in destination_channel_usernames:
            try:
                if destination.startswith('https://t.me/'):
                    channel = await self.client.get_entity(destination)
                else:
                    channel = destination

                if media:
                    await self.client.send_file(channel, media, caption=message)
                else:
                    await self.client.send_message(channel, message)
            except Exception as e:
                print(f"Не вдалося надіслати повідомлення до {destination}: {e}")

    def setup_message_handler(self):
        @self.client.on(events.NewMessage(chats=source_channel_ids))
        async def handle_event(event):
            try:
                await self.forward_message(event.message.message, event.message.media if event.message.media else None)
            except Exception as e:
                print(f'Error while handling event:, {e}')

    async def watch_file(self):
        while True:
            await asyncio.sleep(5)
            try:
                current_modified_time = os.path.getmtime(json_file_path)
                if current_modified_time != self.last_modified_time:
                    self.last_modified_time = current_modified_time
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'content' in data:
                            await self.forward_message(data['content'])
            except Exception as e:
                print(f"Помилка зчитування файлу або надсилання повідомлення: {e}")

    async def start(self):
        await self.client.start()
        print('Telegram client started and watching file for changes...')
        self.setup_message_handler()

        await self.watch_file()

        # Підтримуємо підключення до Telegram
        await self.client.run_until_disconnected()


async def main():
    telegram_bot = TelegramBot(account['api_id'], account['api_hash'])
    await telegram_bot.start()


if __name__ == "__main__":
    asyncio.run(main())
