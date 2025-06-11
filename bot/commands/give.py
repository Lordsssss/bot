import discord
from discord import Interaction, app_commands
from bot.db.user import get_user, update_user_points
from bot.utils.constants import ALLOWED_CHANNEL_ID

@app_commands.command(name="give", description="Give some of your points to another user")
@app_commands.describe(
    user="The user to give points to",
    amount="Amount of points to give (must be positive)"
)
async def give(interaction: Interaction, user: discord.Member, amount: int):
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        return
    
    # Check if amount is valid
    if amount <= 0:
        await interaction.response.send_message("You must give a positive number of points.", ephemeral=True)
        return
    
    giver_id = str(interaction.user.id)
    receiver_id = str(user.id)
    
    # Prevent giving points to self
    if giver_id == receiver_id:
        await interaction.response.send_message("You can't give points to yourself!", ephemeral=True)
        return
    
    # Check if giver has enough points
    giver = await get_user(giver_id)
    if giver["points"] < amount:
        await interaction.response.send_message(f"You only have {giver['points']} points, which is not enough!", ephemeral=True)
        return
    
    # Transfer points
    await update_user_points(giver_id, -amount)
    await update_user_points(receiver_id, amount)
    
    # Get updated balances for both users
    updated_giver = await get_user(giver_id)
    updated_receiver = await get_user(receiver_id)
    
    # Send confirmation message
    await interaction.response.send_message(
        f"{interaction.user.mention} gave {amount} points to {user.mention}!\n"
        f"{interaction.user.display_name}'s new balance: {updated_giver['points']} points\n"
        f"{user.display_name}'s new balance: {updated_receiver['points']} points"
    )