"""
Information commands for crypto trading (prices, charts, portfolio, etc.)
"""
import discord
from discord import Interaction
from datetime import datetime
from typing import List

from bot.crypto.models import CryptoModels
from bot.crypto.portfolio import PortfolioManager
from bot.crypto.constants import CRYPTO_COINS
from bot.crypto.chart_generator import ChartGenerator
from bot.db.user import get_user
from bot.utils.discord_helpers import (
    check_channel_permission, create_embed, send_error_response,
    format_crypto_amount, get_medal_emoji, get_trading_status_emoji
)
from bot.utils.crypto_helpers import (
    validate_ticker, get_available_tickers_string, format_holdings_display,
    format_transaction_history, format_leaderboard_entry, calculate_portfolio_summary
)


async def handle_crypto_prices(interaction: Interaction):
    """View current crypto prices"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        coins = await CryptoModels.get_all_coins()
        if not coins:
            await send_error_response(interaction, "No crypto data available! Market might be initializing...")
            return
        
        # Sort coins by price (highest first)
        coins.sort(key=lambda x: x['current_price'], reverse=True)
        
        price_list = ""
        for coin in coins:
            ticker = coin['ticker']
            name = coin['name']
            price = coin['current_price']
            
            # Get price change from 1 hour ago
            price_history = await CryptoModels.get_price_history(ticker, hours=1)
            change_emoji = "📈" if len(price_history) < 2 else ("📈" if price > price_history[0]['price'] else "📉")
            
            price_list += f"{change_emoji} **{ticker}** ({name})\n"
            price_list += f"    💰 ${price:.4f}\n\n"
        
        embed = create_embed(
            title="🪙 Crypto Market Prices",
            description="Current prices for all available cryptocurrencies",
            fields=[{
                "name": "Current Prices",
                "value": price_list,
                "inline": False
            }],
            footer="Prices update every ~15-30 seconds | Use /crypto charts <ticker> for detailed view"
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error fetching prices: {str(e)}")


async def handle_crypto_charts(interaction: Interaction, ticker: str, timeline: str = "2h"):
    """View price chart for one, multiple, or all cryptos with custom timeline"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        # Parse and validate timeline
        is_valid, hours, error_msg = ChartGenerator.parse_timeline(timeline)
        if not is_valid:
            await send_error_response(interaction, f"Invalid timeline: {error_msg}")
            return
        
        # Handle 'all' case
        if ticker.lower().strip() == 'all':
            all_coins = await CryptoModels.get_all_coins()
            if not all_coins:
                await send_error_response(interaction, "No crypto data available!")
                return
            tickers = [coin['ticker'] for coin in all_coins]
        else:
            tickers = [t.strip().upper() for t in ticker.split(',')]
        
        # Limit to prevent chart overcrowding
        if ticker.lower().strip() == 'all':
            tickers = tickers[:10]
        
        # Validate all tickers exist
        valid_tickers = []
        coin_data = {}
        for t in tickers:
            coin = await CryptoModels.get_coin(t)
            if coin:
                valid_tickers.append(t)
                coin_data[t] = coin
        
        if not valid_tickers:
            if ticker.lower().strip() == 'all':
                await send_error_response(interaction, "No crypto data available!")
            else:
                await send_error_response(interaction, f"No valid cryptos found!\nAvailable: {get_available_tickers_string()}")
            return
        
        # Generate chart using ChartGenerator
        chart_file, embed = await ChartGenerator.generate_chart(valid_tickers, coin_data, hours)
        await interaction.followup.send(embed=embed, file=chart_file)
        
    except Exception as e:
        await send_error_response(interaction, f"Error generating chart: {str(e)}")


async def handle_crypto_portfolio(interaction: Interaction):
    """View user's crypto portfolio"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        portfolio_data = await PortfolioManager.get_portfolio_value(user_id)
        summary = calculate_portfolio_summary(portfolio_data)
        
        # Get user's regular points
        user = await get_user(user_id)
        points = user.get("points", 0)
        
        fields = [
            {
                "name": "📊 Current Portfolio",
                "value": (
                    f"**Current Value:** {summary['current_value']} points\n"
                    f"**Currently Invested:** {summary['current_invested']} points\n"
                    f"**Current P/L:** {summary['current_pl']} points ({summary['current_pl_percent']})"
                ),
                "inline": False
            },
            {
                "name": "🏆 All-Time Performance",
                "value": (
                    f"**Total Ever Invested:** {summary['all_time_invested']} points\n"
                    f"**Total Ever Returned:** {summary['all_time_returned']} points\n"
                    f"**All-Time P/L:** {summary['all_time_pl']} points ({summary['all_time_pl_percent']})"
                ),
                "inline": False
            },
            {
                "name": "💼 Current Holdings",
                "value": format_holdings_display(portfolio_data["holdings"]),
                "inline": False
            },
            {
                "name": "💰 Available Points",
                "value": f"{points:.2f} points",
                "inline": True
            }
        ]
        
        color = 0x00ff00 if portfolio_data["all_time_profit_loss"] >= 0 else 0xff0000
        embed = create_embed(
            title=f"🏦 {interaction.user.display_name}'s Crypto Portfolio",
            color=color,
            fields=fields
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error fetching portfolio: {str(e)}")


async def handle_crypto_leaderboard(interaction: Interaction):
    """View crypto trading leaderboard"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        leaderboard = await PortfolioManager.get_leaderboard(limit=10)
        
        if not leaderboard:
            await interaction.followup.send("📊 No crypto traders yet! Be the first to start trading!")
            return
        
        leaderboard_text = ""
        for i, trader in enumerate(leaderboard, 1):
            try:
                user = await interaction.client.fetch_user(int(trader["user_id"]))
                username = user.display_name
            except:
                username = f"User {trader['user_id'][:8]}..."
            
            leaderboard_text += format_leaderboard_entry(i, username, trader)
        
        embed = create_embed(
            title="🏆 Crypto Trading Leaderboard (All-Time)",
            description="Top traders ranked by all-time profit/loss",
            color=0xffd700,
            fields=[{
                "name": "Top Traders",
                "value": leaderboard_text,
                "inline": False
            }],
            footer="All-time rankings • 📼 = Active trader • 💰 = Cashed out"
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error fetching leaderboard: {str(e)}")


async def handle_crypto_history(interaction: Interaction):
    """View user's recent crypto transactions"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        transactions = await CryptoModels.get_user_transactions(user_id, limit=10)
        
        embed = create_embed(
            title=f"📋 {interaction.user.display_name}'s Transaction History",
            description="Your last 10 crypto transactions",
            color=0x0099ff,
            fields=[{
                "name": "Recent Transactions",
                "value": format_transaction_history(transactions),
                "inline": False
            }],
            footer="Showing last 10 transactions"
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error fetching transaction history: {str(e)}")


