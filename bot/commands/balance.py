import discord
from discord import Interaction,app_commands
from discord.app_commands import command
from bot.db.user import get_user
from bot.utils.discord_helpers import check_channel_permission
from bot.utils.crypto_helpers import format_money
from bot.db.server_config import get_server_language
from bot.utils.translations import get_text

@command(name="balance", description="Check your current point balance")
async def balance(interaction: Interaction):
    if not await check_channel_permission(interaction):
        return
    
    guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
    language = await get_server_language(guild_id)
    
    user = await get_user(str(interaction.user.id))
    message = get_text(
        guild_id, 
        "balance_message", 
        language,
        mention=interaction.user.mention,
        balance=format_money(user['points'])
    )
    
    await interaction.response.send_message(message)
