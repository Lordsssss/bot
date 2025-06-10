from discord import Interaction, app_commands
from bot.db.user import get_user
from bot.utils.constants import ALLOWED_CHANNEL_ID

@discord.app_commands.command(name="limit", description="Check your weekly betting limit status")
async def limit(interaction: Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    user_id = str(interaction.user.id)
    user = await get_user(user_id)
    weekly_spent = user.get("weekly_spent", 0)
    weekly_limit = 1000
    remaining = weekly_limit - weekly_spent

    await interaction.response.send_message(
        f"{interaction.user.mention}, you've used {weekly_spent}/{weekly_limit} points of your weekly betting limit. "
        f"You can bet {remaining} more points this week."
    )
