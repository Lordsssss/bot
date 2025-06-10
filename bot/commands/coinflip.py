import discord
from discord import Interaction,app_commands
from bot.db.user import get_user, update_user_points, check_weekly_limit
from bot.utils.constants import ALLOWED_CHANNEL_ID
import random

@app_commands.command(name="coinflip", description="Bet on a coin flip (1-100 points)")
@app_commands.describe(amount="Amount to bet (max 100)")
async def coinflip(interaction: Interaction, amount: int):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    if amount > 100 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 100 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    can_bet, reason = await check_weekly_limit(user_id, amount)
    if not can_bet:
        await interaction.response.send_message(reason, ephemeral=True)
        return

    user = await get_user(user_id)
    outcome = random.choice(["win", "lose"])
    result = amount if outcome == "win" else -amount
    await update_user_points(user_id, result)

    msg = f"You {'won' if result > 0 else 'lost'} the bet! {'+' if result > 0 else ''}{result} points."
    new_balance = user["points"] + result
    await interaction.response.send_message(f"{interaction.user.mention} {msg} Your new balance is {new_balance}.")
