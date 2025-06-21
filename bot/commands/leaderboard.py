from discord import Interaction, app_commands
from bot.db.connection import users
from bot.utils.discord_helpers import check_channel_permission
from bot.utils.crypto_helpers import format_money
import discord

@discord.app_commands.command(name="leaderboard", description="Show the top 10 users by points")
async def leaderboard(interaction: Interaction):
    if not await check_channel_permission(interaction):
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
        leaderboard_text += f"**#{index}** {name} — {format_money(user['points'])}\n"
        index += 1

    await interaction.response.send_message(leaderboard_text)