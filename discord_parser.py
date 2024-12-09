import asyncio
import json

import discord
from discord.ext import commands
from pars_conf import DISCORD_TOKEN, TARGET_GUILD_ID, json_file_path, TARGET_CHANNEL_ID


intents = discord.Intents.default()
intents.dm_messages = True
intents.guild_typing = True
intents.typing = True
intents.members = True
intents.guild_messages = True
intents.messages = True

client = commands.Bot(command_prefix='!', intents=intents, self_bot=True)


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!\n'
          f'Server count: {len(client.guilds)}\n')


@client.event
async def on_message(message):
    if message.author == client.user:
        print(message.content)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump({'content': message.content}, f)
            f.write('\n')





client.run(DISCORD_TOKEN, bot=False)
