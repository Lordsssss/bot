"""
Server configuration commands for multi-server support
"""
import discord
from discord import Interaction, app_commands
from bot.utils.discord_helpers import check_channel_permission, create_embed, send_error_response, send_success_response
from bot.db.server_config import (
    get_server_config, update_server_language, add_allowed_channel, 
    remove_allowed_channel, clear_allowed_channels, get_server_language
)
from bot.utils.translations import get_text, get_supported_languages, is_language_supported


@app_commands.command(name="config", description="View server configuration")
@app_commands.checks.has_permissions(administrator=True)
async def config_view(interaction: Interaction):
    """View current server configuration"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        config = await get_server_config(guild_id)
        
        # Format allowed channels
        allowed_channels = config.get("allowed_channels", [])
        if not allowed_channels:
            channels_text = get_text(guild_id, "all_channels", language)
        else:
            channel_mentions = []
            for channel_id in allowed_channels:
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    channel_mentions.append(channel.mention)
                else:
                    channel_mentions.append(f"<#{channel_id}> (deleted)")
            channels_text = "\n".join(channel_mentions) if channel_mentions else get_text(guild_id, "no_channels", language)
        
        embed = create_embed(
            title=get_text(guild_id, "config_title", language),
            color=0x3498db,
            fields=[
                {
                    "name": get_text(guild_id, "current_language", language),
                    "value": f"🌐 {language.upper()} ({'Français' if language == 'fr' else 'English'})",
                    "inline": True
                },
                {
                    "name": get_text(guild_id, "allowed_channels", language),
                    "value": channels_text,
                    "inline": False
                }
            ],
            footer="Use /config-language and /config-channel commands to modify settings"
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error viewing config: {str(e)}")


@app_commands.command(name="config-language", description="Set server language")
@app_commands.describe(language="Language code (en for English, fr for French)")
@app_commands.checks.has_permissions(administrator=True)
async def config_language(interaction: Interaction, language: str):
    """Set server language"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        language = language.lower()
        guild_id = str(interaction.guild_id)
        current_language = await get_server_language(guild_id)
        
        if not is_language_supported(language):
            supported = ", ".join(get_supported_languages())
            message = get_text(guild_id, "invalid_language", current_language, languages=supported)
            await send_error_response(interaction, message)
            return
        
        success = await update_server_language(guild_id, language)
        if success:
            # Use the NEW language for the success message
            message = get_text(guild_id, "language_updated", language, language_name=language.upper())
            await send_success_response(interaction, message)
        else:
            message = get_text(guild_id, "error_occurred", current_language, error="Failed to update language")
            await send_error_response(interaction, message)
            
    except Exception as e:
        guild_id = str(interaction.guild_id)
        current_language = await get_server_language(guild_id)
        message = get_text(guild_id, "error_occurred", current_language, error=str(e))
        await send_error_response(interaction, message)


@app_commands.command(name="config-channel-add", description="Add a channel where bot commands are allowed")
@app_commands.describe(channel="Channel to add to allowed list")
@app_commands.checks.has_permissions(administrator=True)
async def config_channel_add(interaction: Interaction, channel: discord.TextChannel):
    """Add a channel to allowed channels list"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        
        success = await add_allowed_channel(guild_id, str(channel.id))
        if success:
            message = get_text(guild_id, "channel_added", language, channel=channel.mention)
            await send_success_response(interaction, message)
        else:
            message = get_text(guild_id, "error_occurred", language, error="Failed to add channel")
            await send_error_response(interaction, message)
            
    except Exception as e:
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        message = get_text(guild_id, "error_occurred", language, error=str(e))
        await send_error_response(interaction, message)


@app_commands.command(name="config-channel-remove", description="Remove a channel from allowed list")
@app_commands.describe(channel="Channel to remove from allowed list")
@app_commands.checks.has_permissions(administrator=True)
async def config_channel_remove(interaction: Interaction, channel: discord.TextChannel):
    """Remove a channel from allowed channels list"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        
        success = await remove_allowed_channel(guild_id, str(channel.id))
        if success:
            message = get_text(guild_id, "channel_removed", language, channel=channel.mention)
            await send_success_response(interaction, message)
        else:
            message = get_text(guild_id, "error_occurred", language, error="Failed to remove channel")
            await send_error_response(interaction, message)
            
    except Exception as e:
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        message = get_text(guild_id, "error_occurred", language, error=str(e))
        await send_error_response(interaction, message)


@app_commands.command(name="config-channel-clear", description="Clear all channel restrictions (allow all channels)")
@app_commands.checks.has_permissions(administrator=True)
async def config_channel_clear(interaction: Interaction):
    """Clear all channel restrictions"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        
        success = await clear_allowed_channels(guild_id)
        if success:
            message = get_text(guild_id, "channels_cleared", language)
            await send_success_response(interaction, message)
        else:
            message = get_text(guild_id, "error_occurred", language, error="Failed to clear channels")
            await send_error_response(interaction, message)
            
    except Exception as e:
        guild_id = str(interaction.guild_id)
        language = await get_server_language(guild_id)
        message = get_text(guild_id, "error_occurred", language, error=str(e))
        await send_error_response(interaction, message)