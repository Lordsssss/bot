from discord.ext import tasks
from bot.db.user import users, get_user
from bot.db.winners import record_weekly_winner
from datetime import datetime, timedelta
import asyncio
from bot.utils.constants import ALLOWED_CHANNEL_ID
import discord
from discord import Interaction,app_commands

def start(client):
    # Weekly reset logic as a separate function to reuse it
    async def perform_weekly_reset(channel=None):
        now = datetime.utcnow()
        if channel:
            winner = await users.find_one(sort=[("points", -1)])
            if winner:
                try:
                    member = await channel.guild.fetch_member(int(winner["_id"]))
                    name = member.display_name
                except Exception:
                    name = f"User ID {winner['_id']}"

                await record_weekly_winner(
                    user_id=winner["_id"],
                    username=name,
                    points=winner["points"],
                    date=now.strftime("%Y-%m-%d"),
                )

                embed = discord.Embed(
                    title="🎉 Weekly Winner 🎉",
                    description=f"**{name}** wins with **{winner['points']}** points!",
                    color=0xFFD700,
                )
                embed.set_footer(text="Points have been reset.")
                await channel.send(embed=embed)

            await users.update_many({"points": {"$lt": 1000}}, {"$set": {"points": 1000}})
            await users.update_many({}, {"$set": {"weekly_spent": 0}})
            print("Weekly reset complete. Users below 1000 points were reset to 1000.")
            return True
        return False

    @tasks.loop(hours=24)
    async def weekly_reset():
        now = datetime.utcnow()
        if now.weekday() == 6:  # Sunday
            channel = client.get_channel(ALLOWED_CHANNEL_ID)
            if channel:
                await perform_weekly_reset(channel)

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
    
    # Admin-only force reset command
    @app_commands.command(name="forcereset", description="Force a weekly reset (admin only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def force_reset(interaction: discord.Interaction):
        channel = client.get_channel(ALLOWED_CHANNEL_ID)
        if channel:
            await interaction.response.defer(ephemeral=True)
            success = await perform_weekly_reset(channel)
            if success:
                await interaction.followup.send("Weekly reset has been forced.", ephemeral=True)
            else:
                await interaction.followup.send("Failed to perform reset.", ephemeral=True)
        else:
            await interaction.response.send_message("Couldn't find the proper channel.", ephemeral=True)

    # Register the command
    client.tree.add_command(force_reset)
    
    return weekly_reset()
