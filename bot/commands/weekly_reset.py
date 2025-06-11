from discord.ext import tasks
from datetime import datetime, timedelta
import asyncio
from bot.utils.constants import ALLOWED_CHANNEL_ID
from bot.commands.force_reset import perform_weekly_reset

def start(client):
    @tasks.loop(hours=24)
    async def weekly_reset():
        now = datetime.utcnow()
        if now.weekday() == 6:  # Sunday
            channel = client.get_channel(ALLOWED_CHANNEL_ID)
            if channel:
                await perform_weekly_reset(client, channel)

    @weekly_reset.before_loop
    async def before():
        await client.wait_until_ready()
        now = datetime.utcnow()
        days = (6 - now.weekday()) % 7
        if days == 0 and now.hour > 0:
            days = 7
        next_reset = datetime(now.year, now.month, now.day) + timedelta(days=days)
        delay = (next_reset - now).total_seconds()
        print(f"Next weekly reset scheduled at {next_reset}")
        await asyncio.sleep(delay)
    
    return weekly_reset()
