from discord import Interaction, app_commands
from bot.db.connection import users
from bot.utils.constants import ALLOWED_CHANNEL_ID
import discord

@discord.app_commands.command(name="leaderboard", description="Show the top 10 users by points")
async def leaderboard(interaction: Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    top_users = users.find().sort("points", -1).limit(10)
    leaderboard_text = "**🏆 Leaderboard 🏆**\n"
    index = 1

    async for user in top_users:
        try:
            member = await interaction.guild.fetch_member(int(user["_id"]))
            name = member.display_name
        except Exception:
            name = f"User ID {user['_id']}"
        leaderboard_text += f"**#{index}** {name} — {user['points']} points\n"
        index += 1

    await interaction.response.send_message(leaderboard_text)