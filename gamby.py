import os
import discord
import random
from discord import app_commands
from discord.ext import commands, tasks
from db import get_user, update_user_points, users, check_and_update_daily_usage, record_weekly_winner, get_winners_history, winners_history
from datetime import datetime, timedelta
import asyncio

ALLOWED_CHANNEL_ID = 1381720147487625258  # 🔒 Restrict commands to this channel

intents = discord.Intents.default()
intents.members = True  # Needed to access member display names
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} (slash commands synced)")
    weekly_reset.start()  # Start the weekly reset task

@tree.command(name="balance", description="Check your current point balance")
async def balance(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore

    user = await get_user(str(interaction.user.id))
    await interaction.response.send_message(
        f"{interaction.user.mention}, your balance is {user['points']} points."
    )

@tree.command(name="coinflip", description="Bet on a coin flip (1-100 points) - once per day")
@app_commands.describe(amount="Amount to bet (max 100)")
async def coinflip(interaction: discord.Interaction, amount: int):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore

    if amount > 100 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 100 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    
    # Check if user already used coinflip today
    can_use = await check_and_update_daily_usage(user_id, "coinflip")
    if not can_use:
        await interaction.response.send_message("You've already used the coinflip command today! Come back tomorrow.", ephemeral=True)
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

# Weekly reset task - runs every Sunday at midnight UTC
@tasks.loop(hours=24)
async def weekly_reset():
    now = datetime.utcnow()
    # Check if it's Sunday (weekday 6)
    if now.weekday() == 6:
        channel = client.get_channel(ALLOWED_CHANNEL_ID)
        if channel:
            # Find the winner before resetting points
            winner = None
            highest_points = 0
            
            async for user_doc in users.find().sort("points", -1).limit(1):
                winner = user_doc
                highest_points = user_doc["points"]
            
            if winner:
                try:
                    # Try to get member info for a nicer display name
                    guild = channel.guild
                    member = await guild.fetch_member(int(winner["_id"]))
                    winner_name = member.display_name
                except:
                    winner_name = f"User ID {winner['_id']}"
                
                # Record the winner in history
                await record_weekly_winner(
                    user_id=winner["_id"],
                    username=winner_name,
                    points=highest_points,
                    date=now.strftime("%Y-%m-%d")
                )
                
                # Announce the winner
                embed = discord.Embed(
                    title="🎉 Weekly Contest Winner! 🎉",
                    description=f"**{winner_name}** won this week's contest with **{highest_points}** points!",
                    color=0xFFD700  # Gold color
                )
                embed.set_footer(text="All points have been reset for the new week. Good luck!")
                await channel.send(embed=embed)
                
                # Reset everyone's points to the starting amount (100)
                await users.update_many({}, {"$set": {"points": 100}})
                
                print(f"Weekly reset completed. Winner: {winner_name} with {highest_points} points")

@weekly_reset.before_loop
async def before_weekly_reset():
    # Wait until the bot is ready before starting the task
    await client.wait_until_ready()
    
    # Calculate time until the next Sunday at midnight UTC
    now = datetime.utcnow()
    days_until_sunday = (6 - now.weekday()) % 7  # 0 if today is Sunday
    if days_until_sunday == 0 and now.hour > 0:  # If Sunday but past midnight
        days_until_sunday = 7
    
    target_time = datetime(now.year, now.month, now.day, 0, 0, 0) + timedelta(days=days_until_sunday)
    seconds_until_target = (target_time - now).total_seconds()
    
    # Sleep until the next Sunday at midnight
    print(f"Scheduling first weekly reset for {target_time} UTC")
    await asyncio.sleep(seconds_until_target)

@tree.command(name="nextweek", description="Check when the next weekly reset happens")
async def next_reset(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return
    
    now = datetime.utcnow()
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0 and now.hour > 0:
        days_until_sunday = 7
    
    hours_remaining = (days_until_sunday * 24) - now.hour
    
    await interaction.response.send_message(
        f"The next weekly reset will happen in {days_until_sunday} days and {now.hour} hours."
    )

@tree.command(name="halloffame", description="View the hall of fame with past weekly winners")
async def hall_of_fame(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore
        
    winners = await get_winners_history(limit=10)
    
    if not winners:
        await interaction.response.send_message("No winners have been recorded yet!")
        return
        
    embed = discord.Embed(
        title="🏆 Hall of Fame - Weekly Winners 🏆",
        description="History of past weekly winners",
        color=0xFFD700
    )
    
    for winner in winners:
        embed.add_field(
            name=f"{winner['date']}",
            value=f"**{winner['username']}** - {winner['points']} points",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@tree.command(name="mywins", description="Check how many times you've won")
async def my_wins(interaction: discord.Interaction):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return  # silently ignore
        
    user_id = str(interaction.user.id)
    count = await winners_history.count_documents({"user_id": user_id})
    
    if count == 0:
        await interaction.response.send_message(f"{interaction.user.mention}, you haven't won any weekly contests yet. Keep trying!")
    elif count == 1:
        await interaction.response.send_message(f"{interaction.user.mention}, you've won 1 weekly contest. Congratulations!")
    else:
        await interaction.response.send_message(f"{interaction.user.mention}, you've won {count} weekly contests. Impressive!")

client.run(os.getenv("DISCORD_TOKEN"))
