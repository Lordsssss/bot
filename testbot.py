import discord
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = os.getenv("DISCORD_TOKEN")

TARGET_USER_IDS = [549283791508602895, 465652511081103370, 305166432893796352]
SPAM_THRESHOLD = 5
SPAM_DETECTION_WINDOW = timedelta(seconds=30)
RESET_COOLDOWN = timedelta(minutes=5)

rage_bait_replies = [
    "yap yap", "we get it, bro", "calm down keyboard warrior", "seek help",
    "touch grass", "you still typing?", "rent free", "you good?",
    "go outside maybe?", "ratio + cringe"
]

rage_gifs = [
    "https://tenor.com/view/sonic-sonic-memes-sonic-the-hedgehog-go-outside-get-out-gif-25164725",
    "https://tenor.com/view/touch-grass-grass-gif-6175076120562349513",
    "https://tenor.com/view/yap-gif-9986526281335654952",
    "https://tenor.com/view/yap-chatter-gibberish-yapping-chatty-gif-6751408675856929437",
    "https://tenor.com/view/yapping-bstchld-beastchild-beast-child-gif-11726866372930981807",
    "https://tenor.com/view/yapping-yapping-level-today-catastrophic-yapanese-gif-13513208407930173397",
    "https://tenor.com/view/ultraman-cursed-meme-cursed-ultraman-yapping-gif-14091335712202744644",
    "https://tenor.com/view/jake-grabbing-emoji-enhypen-jake-enhypen-meme-jake-제이크-gif-26519937",
    "https://tenor.com/view/cursed-emoji-love-cute-emoji-cursed-gif-25283059",
    "https://tenor.com/view/yungblud-emo-uwu-yungblud-emo-yungnlud-uwu-gif-26380984",
    "https://tenor.com/view/dark-mario-wtf-cursed-spoopee-gif-25344970",
    "https://tenor.com/view/skull-skull-skull-skull-skull-skull-skull-skull-gif-14574828933741070167",
    "https://tenor.com/view/get-real-gif-25586253",
    "https://tenor.com/view/get-real-drive-gif-16394762365768463695",
    "https://tenor.com/view/get-real-cat-skate-funny-meme-gif-18666878",
    "https://tenor.com/view/spongebob-get-real-spongebob-get-real-spongebob-face-spongebob-ugly-gif-13309562138513808785",
    "https://tenor.com/view/imaginal-disk-magdalena-bay-spongebob-spongebob-meme-ascending-gif-2351799731105130575",
]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)

# Per-user tracking
user_messages = defaultdict(list)
user_spamming = defaultdict(bool)
user_last_message_time = {}

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot or message.author.id not in TARGET_USER_IDS:
        return

    now = datetime.utcnow()
    user_id = message.author.id

    # Track recent messages (last 30 seconds)
    user_messages[user_id] = [
        t for t in user_messages[user_id]
        if now - t <= SPAM_DETECTION_WINDOW
    ]
    user_messages[user_id].append(now)
    user_last_message_time[user_id] = now

    # Detect spamming
    if len(user_messages[user_id]) >= SPAM_THRESHOLD:
        user_spamming[user_id] = True

    # If spamming, keep replying
    if user_spamming[user_id]:
        # Stop if silence for 5+ minutes
        if now - user_last_message_time[user_id] > RESET_COOLDOWN:
            user_spamming[user_id] = False
            user_messages[user_id] = []
            return

        # Otherwise, send rage bait
        bait = random.choice(rage_bait_replies)
        gif = random.choice(rage_gifs)
        await message.reply(f"{bait}\n{gif}")


client.run(TOKEN)