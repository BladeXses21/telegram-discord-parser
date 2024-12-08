import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Telegram settings

account = config["account"]
source_channel_ids = config["source_channel_ids"]
destination_channel_usernames = config["destination_channel_usernames"]

# Discord settings

DISCORD_TOKEN = config["DISCORD_TOKEN"]
TARGET_GUILD_ID = config["TARGET_GUILD_ID"]

json_file_path = './discord_messages.json'


