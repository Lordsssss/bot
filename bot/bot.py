import os
from discord.ext import commands
from dotenv import load_dotenv
from bot.utils.constants import ALLOWED_CHANNEL_ID
from bot.commands import (
    balance,
    coinflip,
    slot,
    leaderboard,
    hall_of_fame,
    next_reset,
    weekly_limit,
    my_wins,
    weekly_reset,
)

load_dotenv()

intents = commands.Intents.default()
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents)

def start_bot():
    @client.event
    async def on_ready():
        await client.tree.sync()
        print(f"Logged in as {client.user}")
        weekly_reset.start(client)

    client.run(os.getenv("DISCORD_TOKEN"))
