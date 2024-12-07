import asyncio
import json

import discord
from discord.ext import commands
from pars_conf import DISCORD_TOKEN, TARGET_GUILD_ID, json_file_path

client = commands.Bot(command_prefix='!', intents=discord.Intents.all(), self_bot=True)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!\n'
          f'Server count: {len(client.guilds)}')


@client.event
async def on_message(message):
    # Переконаємось, що бот не реагує на власні повідомлення
    if message.author == client.user:
        print(message.content)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump({'content': message.content}, f)
            f.write('\n')

    # Перевіряємо, що повідомлення надіслано на сервер з вказаним ID
    if message.guild and message.guild.id == TARGET_GUILD_ID:
        # Виводимо інформацію про повідомлення в консоль
        content = f"[{message.guild.name} - {message.channel.name}] {message.author}: {message.content}"
        print(content)

        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump({'content': content}, f)
            f.write('\n')


client.run(DISCORD_TOKEN, bot=False)
