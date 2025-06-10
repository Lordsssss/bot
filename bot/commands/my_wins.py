from discord import Interaction
from bot.db.connection import winners_history
from bot.utils.constants import ALLOWED_CHANNEL_ID

@discord.app_commands.command(name="mywins", description="Check how many times you've won")
async def my_wins(interaction: Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    user_id = str(interaction.user.id)
    count = await winners_history.count_documents({"user_id": user_id})

    if count == 0:
        msg = f"{interaction.user.mention}, you haven't won any weekly contests yet. Keep trying!"
    elif count == 1:
        msg = f"{interaction.user.mention}, you've won 1 weekly contest. Congratulations!"
    else:
        msg = f"{interaction.user.mention}, you've won {count} weekly contests. Impressive!"

    await interaction.response.send_message(msg)
