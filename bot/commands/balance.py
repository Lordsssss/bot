from discord import Interaction
from discord.app_commands import command
from bot.db.user import get_user
from bot.utils.constants import ALLOWED_CHANNEL_ID

@command(name="balance", description="Check your current point balance")
async def balance(interaction: Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return
    user = await get_user(str(interaction.user.id))
    await interaction.response.send_message(
        f"{interaction.user.mention}, your balance is {user['points']} points."
    )
