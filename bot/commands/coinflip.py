import discord
from discord import Interaction,app_commands
from bot.db.user import get_user, update_user_points
from bot.utils.discord_helpers import check_channel_permission
from bot.items.models import ItemsManager
import random

@app_commands.command(name="coinflip", description="Bet on a coin flip (1-1000 points)")
@app_commands.describe(amount="Amount to bet (max 1000)")
async def coinflip(interaction: Interaction, amount: int):
    if not await check_channel_permission(interaction):
        return

    if amount > 1000 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 1000 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    user = await get_user(user_id)
    
    # Simple balance check
    if user["points"] < amount:
        await interaction.response.send_message(f"You don't have enough points. Your balance: {user['points']}", ephemeral=True)
        return
    
    # Check for Lucky Charm (improves odds)
    lucky_charm = await ItemsManager.check_effect_active(user_id, "casino_boost")
    
    # Base 50% win chance, boosted by Lucky Charm
    win_chance = 0.5
    if lucky_charm:
        win_chance += lucky_charm["effect_value"]  # +15% from lucky charm
        win_chance = min(win_chance, 0.95)  # Cap at 95%
    
    outcome = "win" if random.random() < win_chance else "lose"
    result = amount if outcome == "win" else -amount
    await update_user_points(user_id, result)

    # Add lucky charm indicator to message
    luck_indicator = " 🍀" if lucky_charm else ""
    msg = f"You {'won' if result > 0 else 'lost'} the bet{luck_indicator}! {'+' if result > 0 else ''}{result} points."
    new_balance = user["points"] + result
    await interaction.response.send_message(f"{interaction.user.mention} {msg} Your new balance is {new_balance}.")
