import discord
import os
import random
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = os.getenv("DISCORD_TOKEN")

TARGET_USER_IDS = [549283791508602895, 465652511081103370, 305166432893796352]
SPAM_THRESHOLD = 7  # messages
TIME_WINDOW = timedelta(minutes=5)

rage_bait_replies = [
    "yap yap",
    "we get it, bro",
    "calm down keyboard warrior",
    "seek help",
    "touch grass",
    "you still typing?",
    "rent free",
    "you good?",
    "go outside maybe?",
    "ratio + cringe"
]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)

# Tracks message timestamps for each user
user_messages = defaultdict(list)
user_last_triggered = {}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.id not in TARGET_USER_IDS:
        return

    now = datetime.utcnow()
    user_id = message.author.id

    # Purge old messages outside the 5 minute window
    user_messages[user_id] = [
        msg_time for msg_time in user_messages[user_id]
        if now - msg_time <= TIME_WINDOW
    ]

    user_messages[user_id].append(now)

    # Only send response if threshold exceeded and not already triggered
    if len(user_messages[user_id]) >= SPAM_THRESHOLD:
        last_trigger = user_last_triggered.get(user_id)
        if not last_trigger or (now - last_trigger > TIME_WINDOW):
            user_last_triggered[user_id] = now
            response = random.choice(rage_bait_replies)
            await message.reply(response)

client.run(TOKEN)
