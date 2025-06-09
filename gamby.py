import os
import discord
import random
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from db import get_user, update_user_points, users

load_dotenv()

intents = discord.Intents.default()
client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user} (slash commands synced)")

@tree.command(name="balance", description="Check your current point balance")
async def balance(interaction: discord.Interaction):
    user = await get_user(str(interaction.user.id))
    await interaction.response.send_message(
        f"{interaction.user.mention}, your balance is {user['points']} points."
    )

@tree.command(name="bet", description="Bet on a coin flip (1-50 points)")
@app_commands.describe(amount="Amount to bet (max 50)")
async def bet(interaction: discord.Interaction, amount: int):
    if amount > 50 or amount <= 0:
        await interaction.response.send_message("You can only bet between 1 and 50 points.", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    user = await get_user(user_id)

    outcome = random.choice(["win", "lose"])
    result = 50 if outcome == "win" else -50
    await update_user_points(user_id, result)

    msg = f"You {'won' if result > 0 else 'lost'} the bet! {'+' if result > 0 else ''}{result} points."
    new_balance = user["points"] + result
    await interaction.response.send_message(f"{interaction.user.mention} {msg} Your new balance is {new_balance}.")

@tree.command(name="leaderboard", description="Show the top 10 users by points")
async def leaderboard(interaction: discord.Interaction):
    top_users = users.find().sort("points", -1).limit(10)
    leaderboard_text = "**🏆 Leaderboard 🏆**\n"

    index = 1
    async for user in top_users:
        member = interaction.guild.get_member(int(user["_id"]))
        name = member.display_name if member else f"User ID {user['_id']}"
        leaderboard_text += f"**#{index}** {name} — {user['points']} points\n"
        index += 1

    await interaction.response.send_message(leaderboard_text)

client.run(os.getenv("DISCORD_TOKEN"))
