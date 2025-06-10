from discord import Interaction, app_commands
from bot.db.winners import get_winners_history
from bot.utils.constants import ALLOWED_CHANNEL_ID
import discord
from discord import Interaction,app_commands

@discord.app_commands.command(name="halloffame", description="View the hall of fame with past weekly winners")
async def hall_of_fame(interaction: Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    winners = await get_winners_history(limit=10)
    if not winners:
        await interaction.response.send_message("No winners have been recorded yet!")
        return

    embed = discord.Embed(
        title="🏆 Hall of Fame - Weekly Winners 🏆",
        description="History of past weekly winners",
        color=0xFFD700,
    )
    for winner in winners:
        embed.add_field(
            name=f"{winner['date']}",
            value=f"**{winner['username']}** - {winner['points']} points",
            inline=False,
        )
    await interaction.response.send_message(embed=embed)
