import os
import discord
from discord.ext import commands
from discord import Interaction,app_commands

from bot.utils.constants import ALLOWED_CHANNEL_ID
from bot.commands import (
    balance,
    coinflip,
    slot,
    roulette,  # Add this import
    leaderboard,
    hall_of_fame,
    next_reset,
    weekly_limit,
    my_wins,
    weekly_reset,
)

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents)

def start_bot():
    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        weekly_reset.start(client)
        # Move the sync here - after all commands are registered
        await client.tree.sync()

    # Register all commands
    client.tree.add_command(balance.balance)
    client.tree.add_command(coinflip.coinflip)
    client.tree.add_command(slot.slot)
    client.tree.add_command(roulette.roulette)  # Add this line
    client.tree.add_command(leaderboard.leaderboard)
    client.tree.add_command(hall_of_fame.hall_of_fame)
    client.tree.add_command(next_reset.next_reset)
    client.tree.add_command(weekly_limit.limit)
    client.tree.add_command(my_wins.my_wins)

    # Force the weekly_reset module to register its command
    weekly_task = weekly_reset.start(client)  # This registers the forcereset command
    
    client.run(os.getenv("DISCORD_TOKEN"))