import discord
from discord import Interaction,app_commands
from bot.db.user import get_user, update_user_points
from bot.utils.constants import ALLOWED_CHANNEL_ID
import random

@app_commands.command(name="slot", description="Spin the slot machine and try your luck!")
@app_commands.describe(
    amount="Amount to bet per machine (max 1000)",
    machines="Number of machines to play (default: 1)"
)
async def slot(interaction: Interaction, amount: int, machines: int = 1):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    if amount > 1000 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 1000 points per machine.", ephemeral=True)
        return

    if machines <= 0:
        await interaction.response.send_message("You must play at least 1 machine.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    user = await get_user(user_id)
    
    # Calculate how many machines they can afford
    affordable_machines = min(machines, user["points"] // amount)
    
    if affordable_machines <= 0:
        await interaction.response.send_message("You don't have enough points to play.", ephemeral=True)
        return
        
    if affordable_machines < machines:
        machines_message = f"\n(You only had enough points for {affordable_machines} machines instead of {machines})"
    else:
        machines_message = ""

    total_bet = amount * affordable_machines
    # Weekly limit check removed, only balance check above

    # Run each machine
    symbols = ["🍒", "🍋", "🍇", "💎", "🔔"]
    total_winnings = 0
    results = []
    
    for i in range(affordable_machines):
        chosen_symbol = random.choice(symbols)
        roll_type = random.choices(["fail", "two_match", "jackpot"], weights=[80, 18, 2])[0]
        
        if roll_type == "jackpot":
            spin = [chosen_symbol] * 3
            win_amount = amount * 5
            outcome = f"💥 JACKPOT! +{win_amount} points!"
        elif roll_type == "two_match":
            other = random.choice([s for s in symbols if s != chosen_symbol])
            spin = [chosen_symbol, chosen_symbol, other]
            random.shuffle(spin)
            win_amount = int(amount * 1.5)
            outcome = f"✨ Two matches! +{win_amount} points!"
        else:
            spin = random.sample(symbols, 3)
            while len(set(spin)) < 3:
                spin = random.sample(symbols, 3)
            win_amount = -amount
            outcome = f"😢 No match! -{amount} points."
            
        total_winnings += win_amount
        slot_display = f"{' | '.join(spin)}"
        results.append(f"🎰 Machine #{i+1}: {slot_display} → {outcome}")
    
    await update_user_points(user_id, total_winnings)
    new_balance = user["points"] + total_winnings
    
    result_message = "\n".join(results)
    summary = f"Total bet: {total_bet} points\nTotal result: {total_winnings} points\nNew balance: {new_balance} points"
    
    await interaction.response.send_message(
        f"🎰 **Slot Machines** 🎰\n{result_message}\n\n{summary}{machines_message}"
    )

