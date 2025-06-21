import discord
from discord import Interaction,app_commands
from bot.db.user import get_user, update_user_points
from bot.utils.discord_helpers import check_channel_permission
from bot.items.models import ItemsManager
import random

@app_commands.command(name="slot", description="Spin the slot machine and try your luck!")
@app_commands.describe(
    amount="Amount to bet per machine (max 1000)",
    machines="Number of machines to play (default: 1)"
)
async def slot(interaction: Interaction, amount: int, machines: int = 1):
    if not await check_channel_permission(interaction):
        return

    if amount > 1000 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 1000 points per machine.", ephemeral=True)
        return

    if machines <= 0:
        await interaction.response.send_message("You must play at least 1 machine.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    user = await get_user(user_id)
    
    # Check for Lucky Charm (improves odds)
    lucky_charm = await ItemsManager.check_effect_active(user_id, "casino_boost")
    
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
        
        # Base odds: 80% fail, 18% two-match, 2% jackpot
        # Lucky Charm improves odds by reducing fail chance
        if lucky_charm:
            weights = [65, 25, 10]  # Lucky charm: 65% fail, 25% two-match, 10% jackpot
        else:
            weights = [80, 18, 2]   # Normal: 80% fail, 18% two-match, 2% jackpot
            
        roll_type = random.choices(["fail", "two_match", "jackpot"], weights=weights)[0]
        
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
    
    # Add lucky charm indicator to message
    luck_indicator = " 🍀" if lucky_charm else ""
    result_message = "\n".join(results)
    summary = f"Total bet: {total_bet} points\nTotal result: {total_winnings} points\nNew balance: {new_balance} points"
    
    await interaction.response.send_message(
        f"🎰 **Slot Machines{luck_indicator}** 🎰\n{result_message}\n\n{summary}{machines_message}"
    )

