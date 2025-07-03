import discord
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

SOURCE_CHANNEL_ID = 123456789012345678  # Replace with your source channel ID
TARGET_CHANNEL_ID = 876543210987654321  # Replace with your target channel ID

@client.event
async def on_ready():
print(f"Bot is online as {client.user}")

@client.event
async def on_message(message):
if message.channel.id == SOURCE_CHANNEL_ID and not message.author.bot:
target = client.get_channel(TARGET_CHANNEL_ID)
await target.send(f"{message.author.display_name}: {message.content}")

client.run(TOKEN)

