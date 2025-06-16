"""
Server configuration management for multi-server support
"""
from bot.db.connection import db

# Collection for server configurations
server_configs = db["server_configs"]

async def get_server_config(guild_id: str) -> dict:
    """Get server configuration, create default if not exists"""
    config = await server_configs.find_one({"guild_id": guild_id})
    if not config:
        # Create default configuration
        config = {
            "guild_id": guild_id,
            "language": "en",  # Default to English
            "allowed_channels": [],  # Empty means all channels allowed
            "admin_roles": [],  # Roles that can configure the bot
            "created_at": None
        }
        await server_configs.insert_one(config)
    return config

async def update_server_language(guild_id: str, language: str) -> bool:
    """Update server language setting"""
    try:
        result = await server_configs.update_one(
            {"guild_id": guild_id},
            {"$set": {"language": language}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except Exception:
        return False

async def add_allowed_channel(guild_id: str, channel_id: str) -> bool:
    """Add a channel to the allowed channels list"""
    try:
        result = await server_configs.update_one(
            {"guild_id": guild_id},
            {"$addToSet": {"allowed_channels": channel_id}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    except Exception:
        return False

async def remove_allowed_channel(guild_id: str, channel_id: str) -> bool:
    """Remove a channel from the allowed channels list"""
    try:
        result = await server_configs.update_one(
            {"guild_id": guild_id},
            {"$pull": {"allowed_channels": channel_id}}
        )
        return result.modified_count > 0
    except Exception:
        return False

async def is_channel_allowed(guild_id: str, channel_id: str) -> bool:
    """Check if a channel is allowed for bot commands"""
    config = await get_server_config(guild_id)
    allowed_channels = config.get("allowed_channels", [])
    
    # If no channels configured, allow all channels
    if not allowed_channels:
        return True
    
    # Check if current channel is in allowed list
    return str(channel_id) in allowed_channels

async def get_server_language(guild_id: str) -> str:
    """Get the language setting for a server"""
    config = await get_server_config(guild_id)
    return config.get("language", "en")

async def clear_allowed_channels(guild_id: str) -> bool:
    """Clear all allowed channels (allows all channels)"""
    try:
        result = await server_configs.update_one(
            {"guild_id": guild_id},
            {"$set": {"allowed_channels": []}}
        )
        return result.modified_count > 0
    except Exception:
        return False