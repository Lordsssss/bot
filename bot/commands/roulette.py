import discord
from discord import Interaction,app_commands
from bot.db.user import get_user, update_user_points, check_weekly_limit
from bot.utils.constants import ALLOWED_CHANNEL_ID
import random

# Roulette wheel numbers with their colors
ROULETTE_WHEEL = {
    0: "green", 1: "red", 2: "black", 3: "red", 4: "black", 5: "red", 6: "black",
    7: "red", 8: "black", 9: "red", 10: "black", 11: "black", 12: "red", 13: "black",
    14: "red", 15: "black", 16: "red", 17: "black", 18: "red", 19: "red", 20: "black",
    21: "red", 22: "black", 23: "red", 24: "black", 25: "red", 26: "black", 27: "red",
    28: "black", 29: "black", 30: "red", 31: "black", 32: "red", 33: "black", 34: "red",
    35: "black", 36: "red"
}

RED_NUMBERS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
BLACK_NUMBERS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

@app_commands.command(name="roulette", description="Play roulette! Bet on number (35:1), red/black (1:1), or odd/even (1:1)")
@app_commands.describe(
    amount="Amount to bet (1-100 points)",
    bet_type="Type of bet: 'number', 'red', 'black', 'odd', 'even'",
    number="Specific number to bet on (0-36, only needed for number bets)"
)
@app_commands.choices(bet_type=[
    app_commands.Choice(name="Number (35:1 payout)", value="number"),
    app_commands.Choice(name="Red (1:1 payout)", value="red"),
    app_commands.Choice(name="Black (1:1 payout)", value="black"),
    app_commands.Choice(name="Odd (1:1 payout)", value="odd"),
    app_commands.Choice(name="Even (1:1 payout)", value="even"),
])
async def roulette(interaction: Interaction, amount: int, bet_type: str, number: int = None):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    # Validate bet amount
    if amount > 100 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 100 points.", ephemeral=True)
        return

    # Validate number bet
    if bet_type == "number":
        if number is None:
            await interaction.response.send_message("You must specify a number (0-36) when betting on a specific number.", ephemeral=True)
            return
        if number < 0 or number > 36:
            await interaction.response.send_message("Number must be between 0 and 36.", ephemeral=True)
            return

    user_id = str(interaction.user.id)
    
    # Check weekly limit
    can_bet, reason = await check_weekly_limit(user_id, amount)
    if not can_bet:
        await interaction.response.send_message(reason, ephemeral=True)
        return

    user = await get_user(user_id)
    
    # Spin the wheel
    winning_number = random.randint(0, 36)
    winning_color = ROULETTE_WHEEL[winning_number]
    
    # Determine if bet won and calculate payout
    won = False
    payout_multiplier = 0
    
    if bet_type == "number":
        if number == winning_number:
            won = True
            payout_multiplier = 35  # 35:1 payout for number bets
    elif bet_type == "red":
        if winning_number in RED_NUMBERS:
            won = True
            payout_multiplier = 1  # 1:1 payout for color bets
    elif bet_type == "black":
        if winning_number in BLACK_NUMBERS:
            won = True
            payout_multiplier = 1  # 1:1 payout for color bets
    elif bet_type == "odd":
        if winning_number != 0 and winning_number % 2 == 1:
            won = True
            payout_multiplier = 1  # 1:1 payout for odd/even bets
    elif bet_type == "even":
        if winning_number != 0 and winning_number % 2 == 0:
            won = True
            payout_multiplier = 1  # 1:1 payout for odd/even bets

    # Calculate result
    if won:
        winnings = amount * payout_multiplier
        result = winnings  # Player gets their bet back plus winnings
    else:
        result = -amount  # Player loses their bet

    # Update user points
    await update_user_points(user_id, result)
    new_balance = user["points"] + result

    # Create result message
    color_emoji = "🟢" if winning_color == "green" else "🔴" if winning_color == "red" else "⚫"
    
    if bet_type == "number":
        bet_description = f"number {number}"
    else:
        bet_description = bet_type
    
    if won:
        if bet_type == "number":
            msg = f"🎉 **JACKPOT!** The ball landed on {winning_number} {color_emoji}!\nYou bet on {bet_description} and won **{winnings} points** (35:1 payout)!"
        else:
            msg = f"🎉 **Winner!** The ball landed on {winning_number} {color_emoji}!\nYou bet on {bet_description} and won **{winnings} points**!"
    else:
        msg = f"💸 The ball landed on {winning_number} {color_emoji}.\nYou bet on {bet_description} and lost **{amount} points**."

    final_msg = f"{interaction.user.mention}\n{msg}\nYour new balance is **{new_balance} points**."
    
    await interaction.response.send_message(final_msg)