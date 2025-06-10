import discord
from discord import Interaction,app_commands
from bot.db.user import get_user, update_user_points, check_weekly_limit
from bot.utils.constants import ALLOWED_CHANNEL_ID
import random

@app_commands.command(name="slot", description="Spin the slot machine and try your luck!")
@app_commands.describe(amount="Amount to bet (max 50)")
async def slot(interaction: Interaction, amount: int):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    if amount > 50 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 50 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    can_bet, reason = await check_weekly_limit(user_id, amount)
    if not can_bet:
        await interaction.response.send_message(reason, ephemeral=True)
        return

    user = await get_user(user_id)
    symbols = ["🍒", "🍋", "🍇", "💎", "🔔"]
    chosen_symbol = random.choice(symbols)

    roll_type = random.choices(["fail", "two_match", "jackpot"], weights=[80, 18, 2])[0]
    if roll_type == "jackpot":
        spin = [chosen_symbol] * 3
        result = amount * 5
        outcome = f"💥 JACKPOT! You won {result} points!"
    elif roll_type == "two_match":
        other = random.choice([s for s in symbols if s != chosen_symbol])
        spin = [chosen_symbol, chosen_symbol, other]
        random.shuffle(spin)
        result = int(amount * 1.5)
        outcome = f"✨ You matched 2 symbols and won {result} points!"
    else:
        spin = random.sample(symbols, 3)
        while len(set(spin)) < 3:
            spin = random.sample(symbols, 3)
        result = -amount
        outcome = f"😢 No match! You lost {amount} points."

    await update_user_points(user_id, result)
    new_balance = user["points"] + result
    slot_display = f"{' | '.join(spin)}"
    await interaction.response.send_message(
        f"🎰 **Slot Machine** 🎰\n{slot_display}\n{outcome}\nYour new balance is {new_balance} points."
    )

