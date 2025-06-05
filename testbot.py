import discord
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # Get token from environment variable
TARGET_USER_IDS = [549283791508602895, 465652511081103370]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.id in TARGET_USER_IDS and not message.author.bot:
        await message.reply("Yap Yap")

client.run(TOKEN)
