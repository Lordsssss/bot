from discord import Interaction
from datetime import datetime
from bot.utils.constants import ALLOWED_CHANNEL_ID
import discord

@discord.app_commands.command(name="nextweek", description="Check when the next weekly reset happens")
async def next_reset(interaction: Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    now = datetime.utcnow()
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.hour > 0:
        days_until_sunday = 7

    hours_remaining = (days_until_sunday * 24) - now.hour
    await interaction.response.send_message(
        f"The next weekly reset will happen in {days_until_sunday} days and {now.hour} hours."
    )

