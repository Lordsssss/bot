from discord import Interaction, app_commands
from bot.db.winners import get_winners_history
from bot.utils.discord_helpers import check_channel_permission
from bot.utils.crypto_helpers import format_money
import discord

@discord.app_commands.command(name="halloffame", description="View the hall of fame with past weekly winners")
async def hall_of_fame(interaction: Interaction):
    if not await check_channel_permission(interaction):
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
            value=f"**{winner['username']}** - {format_money(winner['points'])}",
            inline=False,
        )
    await interaction.response.send_message(embed=embed)
