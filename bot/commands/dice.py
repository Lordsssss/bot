import discord
from discord import Interaction, app_commands
import random
import asyncio
from bot.db.user import get_user, update_user_points
from bot.utils.constants import ALLOWED_CHANNEL_ID
from enum import Enum

# Add dice face Unicode characters
DICE_FACES = {
    1: "⚀",
    2: "⚁", 
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅"
}

class HighLowChoice(Enum):
    HIGHER = "higher"
    LOWER = "lower"

class OddEvenChoice(Enum):
    ODD = "odd"
    EVEN = "even"

class DiceMode(Enum):
    HIGHLOW = "highlow"
    EXACT = "exact"
    ODDEVEN = "oddeven"
    TRIPLE = "triple"

@app_commands.command(name="dice", description="Play various dice games")
@app_commands.describe(
    mode="Game mode to play",
    amount="Amount to bet (1-1000 points)",
    highlow="Predict if the roll will be higher or lower than 10",
    target="Predict the exact sum of the dice (3-18)",
    oddeven="Predict if the sum will be odd or even"
)
@app_commands.choices(
    mode=[
        app_commands.Choice(name="High/Low (>10 or <10)", value="highlow"),
        app_commands.Choice(name="Exact Sum (3-18)", value="exact"),
        app_commands.Choice(name="Odd/Even Sum", value="oddeven"),
        app_commands.Choice(name="Triple (all dice match)", value="triple")
    ],
    highlow=[
        app_commands.Choice(name="Higher than 10", value="higher"),
        app_commands.Choice(name="Lower than 10", value="lower")
    ],
    oddeven=[
        app_commands.Choice(name="Odd Sum", value="odd"),
        app_commands.Choice(name="Even Sum", value="even")
    ]
)
async def dice(
    interaction: Interaction, 
    mode: str, 
    amount: int, 
    highlow: str = None, 
    target: int = None, 
    oddeven: str = None
):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return
    
    # Validate bet amount
    if amount < 1 or amount > 1000:
        await interaction.response.send_message("You can only bet between 1 and 1000 points.", ephemeral=True)
        return

    # Get user data
    user_id = str(interaction.user.id)
    user = await get_user(user_id)
    
    # Check if user has enough points
    if user["points"] < amount:
        await interaction.response.send_message(f"You don't have enough points. Your balance: {user['points']}", ephemeral=True)
        return
    
    # Defer the response to allow for animation
    await interaction.response.defer()
    
    # Initialize the animation message
    message = await interaction.followup.send("🎲 **Rolling dice...** 🎲")
    
    # Show "animation" by editing the message a few times
    for _ in range(3):
        await asyncio.sleep(0.7)
        temp_dice = [random.randint(1, 6) for _ in range(3)]
        temp_dice_emojis = " ".join([DICE_FACES[d] for d in temp_dice])
        temp_dice_sum = sum(temp_dice)
        await message.edit(content=f"🎲 **Rolling dice...** 🎲\n{temp_dice_emojis} (Sum: {temp_dice_sum})")
    
    # Roll the actual dice for the real result
    dice_values = [random.randint(1, 6) for _ in range(3)]
    dice_sum = sum(dice_values)
    dice_str = " + ".join([str(d) for d in dice_values])
    dice_emojis = " ".join([DICE_FACES[d] for d in dice_values])
    
    # Check win conditions based on mode
    win = False
    payout_multiplier = 0
    result_msg = ""
    game_mode = DiceMode(mode)
    
    if game_mode == DiceMode.HIGHLOW:
        if highlow is None:
            await message.edit(content="You need to specify higher or lower for this mode.")
            return
        
        choice = HighLowChoice(highlow)
        if (choice == HighLowChoice.HIGHER and dice_sum > 10) or (choice == HighLowChoice.LOWER and dice_sum < 10):
            win = True
            payout_multiplier = 2  # 2x payout
            result_msg = f"You chose {choice.value}, the sum is {dice_sum} which is {choice.value} than 10!"
        else:
            win = False
            payout_multiplier = 0
            result_msg = f"You chose {choice.value}, but the sum is {dice_sum}!"
        
        # Edge case - if sum is exactly 10
        if dice_sum == 10:
            win = False
            payout_multiplier = 0
            result_msg = f"Sum is exactly 10 - neither higher nor lower. House wins!"
    
    elif game_mode == DiceMode.EXACT:
        if target is None or target < 3 or target > 18:
            await message.edit(content="Please select a valid target sum between 3 and 18.")
            return
        
        if dice_sum == target:
            win = True
            # Higher payout for harder targets (edges have lower probability)
            if target <= 5 or target >= 16:
                payout_multiplier = 10
            elif target <= 7 or target >= 14:
                payout_multiplier = 6
            elif target <= 9 or target >= 12:
                payout_multiplier = 4
            else:
                payout_multiplier = 3
            result_msg = f"You predicted {target} and rolled exactly {dice_sum}! Amazing!"
        else:
            win = False
            payout_multiplier = 0
            result_msg = f"You predicted {target}, but rolled {dice_sum}."
    
    elif game_mode == DiceMode.ODDEVEN:
        if oddeven is None:
            await message.edit(content="You need to specify odd or even for this mode.")
            return
            
        choice = OddEvenChoice(oddeven)
        is_odd = dice_sum % 2 == 1
        
        if (choice == OddEvenChoice.ODD and is_odd) or (choice == OddEvenChoice.EVEN and not is_odd):
            win = True
            payout_multiplier = 2.5  # 2.5x payout
            result_msg = f"You chose {choice.value}, and the sum {dice_sum} is {choice.value}!"
        else:
            win = False
            payout_multiplier = 0
            result_msg = f"You chose {choice.value}, but the sum {dice_sum} is {'odd' if is_odd else 'even'}."
    
    elif game_mode == DiceMode.TRIPLE:
        # Check if all dice have the same value
        if dice_values[0] == dice_values[1] == dice_values[2]:
            win = True
            payout_multiplier = 15  # 15x payout
            result_msg = f"TRIPLE {dice_values[0]}s! JACKPOT!"
        else:
            win = False
            payout_multiplier = 0
            result_msg = f"No triple. Better luck next time!"
    
    # Calculate winnings
    winnings = int(amount * payout_multiplier) if win else -amount
    new_balance = user["points"] + winnings
    
    # Update user points
    await update_user_points(user_id, winnings)
    
    # Create embed response
    embed = discord.Embed(
        title="🎲 Dice Game 🎲",
        description=f"**Mode: {game_mode.name}**\n\n"
                    f"**Dice: {dice_emojis}**\n"
                    f"**Sum: {dice_str} = {dice_sum}**\n\n"
                    f"{result_msg}\n\n"
                    f"**{'WIN!' if win else 'LOSS!'}** {'+' if winnings > 0 else ''}{winnings} points",
        color=0x00FF00 if win else 0xFF0000
    )
    embed.set_footer(text=f"New balance: {new_balance} points | Bet: {amount} points")
    
    # Update the message with the final result
    await message.edit(content=None, embed=embed)