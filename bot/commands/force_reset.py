import discord
from discord import Interaction, app_commands
from bot.utils.constants import ALLOWED_CHANNEL_ID
from bot.db.user import users
from bot.db.winners import record_weekly_winner
from bot.crypto.models import CryptoModels
from datetime import datetime

# Extract the weekly reset logic so it can be shared
async def perform_weekly_reset(client, channel=None):
    now = datetime.utcnow()
    if channel:
        # Get points winner
        winner = await users.find_one(sort=[("points", -1)])
        points_winner_name = None
        if winner:
            try:
                member = await channel.guild.fetch_member(int(winner["_id"]))
                points_winner_name = member.display_name
            except Exception:
                points_winner_name = f"User ID {winner['_id']}"

            await record_weekly_winner(
                user_id=winner["_id"],
                username=points_winner_name,
                points=winner["points"],
                date=now.strftime("%Y-%m-%d"),
            )

        # Get crypto winner
        crypto_portfolios = await CryptoModels.get_weekly_crypto_leaderboard()
        crypto_winner = None
        crypto_winner_name = None
        best_coin = "N/A"
        best_coin_pnl = 0.0
        
        if crypto_portfolios and len(crypto_portfolios) > 0:
            crypto_winner = crypto_portfolios[0]
            try:
                member = await channel.guild.fetch_member(int(crypto_winner["user_id"]))
                crypto_winner_name = member.display_name
            except Exception:
                crypto_winner_name = f"User ID {crypto_winner['user_id']}"
            
            # Find best performing coin for this user
            holdings = crypto_winner.get("holdings", {})
            cost_basis = crypto_winner.get("cost_basis", {})
            if holdings:
                best_pnl = float('-inf')
                for ticker in holdings.keys():
                    # Get current coin price
                    coin = await CryptoModels.get_coin(ticker)
                    if coin and ticker in cost_basis:
                        current_value = holdings[ticker] * coin["current_price"]
                        cost = cost_basis[ticker]
                        coin_pnl = current_value - cost
                        if coin_pnl > best_pnl:
                            best_pnl = coin_pnl
                            best_coin = ticker
                            best_coin_pnl = coin_pnl

            await CryptoModels.record_weekly_crypto_winner(
                user_id=crypto_winner["user_id"],
                username=crypto_winner_name,
                weekly_pnl=crypto_winner.get("all_time_profit_loss", 0.0),
                portfolio_value=crypto_winner.get("total_invested", 0.0),
                best_coin=best_coin,
                best_coin_pnl=best_coin_pnl,
                date=now.strftime("%Y-%m-%d")
            )

        # Create combined winner announcement
        embed = discord.Embed(
            title="🎉 Weekly Winners 🎉",
            color=0xFFD700,
        )
        
        if winner:
            embed.add_field(
                name="🎲 Points Champion",
                value=f"**{points_winner_name}** with **{winner['points']}** points!",
                inline=False
            )
        
        if crypto_winner:
            pnl = crypto_winner.get("all_time_profit_loss", 0.0)
            portfolio_value = crypto_winner.get("total_invested", 0.0)
            embed.add_field(
                name="📈 Crypto Champion",
                value=f"**{crypto_winner_name}** with **${pnl:.2f}** P/L\nBest coin: **{best_coin}** (${best_coin_pnl:.2f})",
                inline=False
            )
        
        embed.set_footer(text="All systems have been reset for a fresh start!")
        await channel.send(embed=embed)

        # Reset all systems
        await users.update_many({"points": {"$lt": 1000}}, {"$set": {"points": 1000}})
        await users.update_many({}, {"$set": {"weekly_spent": 0}})
        await CryptoModels.reset_crypto_system()
        
        print("Weekly reset complete: points reset, crypto system wiped, winners recorded.")
        return True
    return False

@app_commands.command(name="forcereset", description="Force a weekly reset (admin only)")
@app_commands.checks.has_permissions(administrator=True)
async def force_reset(interaction: Interaction):
    client = interaction.client
    channel = client.get_channel(ALLOWED_CHANNEL_ID)
    if channel:
        await interaction.response.defer(ephemeral=True)
        success = await perform_weekly_reset(client, channel)
        if success:
            await interaction.followup.send("Weekly reset has been forced.", ephemeral=True)
        else:
            await interaction.followup.send("Failed to perform reset.", ephemeral=True)
    else:
        await interaction.response.send_message("Couldn't find the proper channel.", ephemeral=True)