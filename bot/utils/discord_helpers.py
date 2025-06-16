"""
Discord utility functions for common operations
"""
import discord
from datetime import datetime
from typing import Optional, List, Dict, Any
from .constants import ALLOWED_CHANNEL_ID, ADMIN_ROLE_ID
from bot.db.server_config import is_channel_allowed, get_server_language
from bot.utils.translations import get_text


def create_embed(
    title: str,
    description: str = "",
    color: int = 0x00ff00,
    fields: Optional[List[Dict[str, Any]]] = None,
    footer: Optional[str] = None,
    timestamp: bool = True
) -> discord.Embed:
    """Create a standardized Discord embed"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow() if timestamp else None
    )
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )
    
    if footer:
        embed.set_footer(text=footer)
    
    return embed


def create_error_embed(message: str) -> discord.Embed:
    """Create a standardized error embed"""
    return create_embed(
        title="❌ Error",
        description=message,
        color=0xff0000
    )


def create_success_embed(message: str) -> discord.Embed:
    """Create a standardized success embed"""
    return create_embed(
        title="✅ Success",
        description=message,
        color=0x00ff00
    )


async def check_channel_permission(interaction) -> bool:
    """Check if command is used in allowed channel for this server"""
    guild_id = str(interaction.guild_id) if interaction.guild_id else None
    if not guild_id:
        return True  # Allow DMs or handle as needed
    
    # Check if channel is allowed for this server
    if not await is_channel_allowed(guild_id, str(interaction.channel_id)):
        language = await get_server_language(guild_id)
        message = get_text(guild_id, "channel_not_allowed", language)
        await interaction.response.send_message(f"❌ {message}", ephemeral=True)
        return False
    return True


async def check_admin_permission(interaction) -> bool:
    """Check if user has admin permissions"""
    if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "❌ This command requires the 'spy' role!", 
            ephemeral=True
        )
        return False
    return True


def format_currency(amount: float, decimals: int = 2) -> str:
    """Format currency with consistent decimal places"""
    return f"{amount:.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with + prefix for positive values"""
    return f"{value:+.{decimals}f}%"


def format_crypto_amount(amount: float) -> str:
    """Format crypto amounts with 3 decimal places"""
    return f"{amount:.3f}"


async def send_error_response(interaction, message: str):
    """Send standardized error response"""
    embed = create_error_embed(message)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def send_success_response(interaction, message: str):
    """Send standardized success response"""
    embed = create_success_embed(message)
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed)
    else:
        await interaction.response.send_message(embed=embed)


def get_impact_color(impact: float) -> int:
    """Get color based on impact value"""
    if impact > 0.3:
        return 0x00ff00  # Bright green for big pumps
    elif impact > 0.1:
        return 0x90EE90  # Light green for moderate pumps
    elif impact > -0.1:
        return 0xffff00  # Yellow for neutral
    elif impact > -0.3:
        return 0xffa500  # Orange for moderate dumps
    else:
        return 0xff0000  # Red for big crashes


def get_impact_emoji(impact: float) -> str:
    """Get emoji based on impact value"""
    if impact > 0.3:
        return "📈🚀"
    elif impact > 0.1:
        return "📈"
    elif impact > -0.1:
        return "➡️"
    elif impact > -0.3:
        return "📉"
    else:
        return "📉💥"


def get_trading_status_emoji(has_holdings: bool) -> str:
    """Get emoji for trading status"""
    return "📼" if has_holdings else "💰"


def get_medal_emoji(position: int) -> str:
    """Get medal emoji for leaderboard position"""
    if position == 1:
        return "🥇"
    elif position == 2:
        return "🥈" 
    elif position == 3:
        return "🥉"
    else:
        return f"{position}."