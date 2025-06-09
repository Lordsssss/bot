import os
import discord
import random
from discord import app_commands
from discord.ext import commands
from db import get_user, update_user_points, users, check_and_update_daily_usage

ALLOWED_CHANNEL_ID = 1381720147487625258  # 🔒 Restrict commands to this channel

intents = discord.Intents.default()
intents.members = True  # Needed to access member display names
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} (slash commands synced)")

@tree.command(name="balance", description="Check your current point balance")
async def balance(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore

    user = await get_user(str(interaction.user.id))
    await interaction.response.send_message(
        f"{interaction.user.mention}, your balance is {user['points']} points."
    )

@tree.command(name="bet", description="Bet on a coin flip (1-50 points) - once per day")
@app_commands.describe(amount="Amount to bet (max 50)")
async def bet(interaction: discord.Interaction, amount: int):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore

    if amount > 50 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 50 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    
    # Check if user already used bet today
    can_use = await check_and_update_daily_usage(user_id, "bet")
    if not can_use:
        await interaction.response.send_message("You've already used the bet command today! Come back tomorrow.", ephemeral=True)
        return
        
    user = await get_user(user_id)

    outcome = random.choice(["win", "lose"])
    result = amount if outcome == "win" else -amount
    await update_user_points(user_id, result)

    msg = f"You {'won' if result > 0 else 'lost'} the bet! {'+' if result > 0 else ''}{result} points."
    new_balance = user["points"] + result
    await interaction.response.send_message(f"{interaction.user.mention} {msg} Your new balance is {new_balance}.")

@tree.command(name="leaderboard", description="Show the top 10 users by points")
async def leaderboard(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore

    top_users = users.find().sort("points", -1).limit(10)
    leaderboard_text = "**🏆 Leaderboard 🏆**\n"

    index = 1
    async for user in top_users:
        try:
            member = await interaction.guild.fetch_member(int(user["_id"]))
            name = member.display_name
        except:
            name = f"User ID {user['_id']}"
        leaderboard_text += f"**#{index}** {name} — {user['points']} points\n"
        index += 1

    await interaction.response.send_message(leaderboard_text)

import random

@tree.command(name="slot", description="Spin the slot machine and try your luck! - once per day")
@app_commands.describe(amount="Amount to bet (max 50)")
async def slot(interaction: discord.Interaction, amount: int):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return

    if amount > 50 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 50 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    
    # Check if user already used slot today
    can_use = await check_and_update_daily_usage(user_id, "slot")
    if not can_use:
        await interaction.response.send_message("You've already used the slot machine today! Come back tomorrow.", ephemeral=True)
        return
        
    user = await get_user(user_id)

    symbols = ["🍒", "🍋", "🍇", "💎", "🔔"]
    chosen_symbol = random.choice(symbols)

    roll_type = random.choices(
        population=["fail", "two_match", "jackpot"],
        weights=[80, 18, 2],
        k=1
    )[0]

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
        while len(set(spin)) < 3:  # force no match
            spin = random.sample(symbols, 3)
        result = -amount
        outcome = f"😢 No match! You lost {amount} points."

    await update_user_points(user_id, result)
    new_balance = user["points"] + result

    slot_display = f"{' | '.join(spin)}"
    await interaction.response.send_message(
        f"🎰 **Slot Machine** 🎰\n{slot_display}\n{outcome}\nYour new balance is {new_balance} points."
    )


client.run(os.getenv("DISCORD_TOKEN"))
