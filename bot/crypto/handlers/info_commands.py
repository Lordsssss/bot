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


async def handle_crypto_analysis(interaction: Interaction, ticker: str = None):
    """View detailed market analysis for skilled trading"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        # Get available tickers
        all_coins = await CryptoModels.get_all_coins()
        available_tickers = [coin["ticker"] for coin in all_coins]
        
        if ticker:
            ticker = ticker.upper()
            if ticker not in available_tickers:
                await send_error_response(interaction, f"Invalid ticker! Available: {', '.join(available_tickers)}")
                return
            
            # Get analysis for specific coin
            if hasattr(interaction.client, 'crypto_manager') and hasattr(interaction.client.crypto_manager, 'advanced_simulator'):
                analysis = await interaction.client.crypto_manager.advanced_simulator.get_market_analysis(ticker)
                
                if analysis:
                    embed = create_embed(
                        title=f"📊 Market Analysis - {ticker}",
                        description=f"Technical analysis for skilled traders",
                        color=0x3498db
                    )
                    
                    current_price = analysis.get("current_price", 0)
                    embed.add_field(
                        name="💰 Current Price",
                        value=f"${current_price:.6f}",
                        inline=True
                    )
                    
                    market_phase = analysis.get("market_phase", "unknown")
                    phase_emoji = {"bull": "🐂", "bear": "🐻", "volatile": "⚡", "normal": "📈"}.get(market_phase, "❓")
                    embed.add_field(
                        name="🌊 Market Phase",
                        value=f"{phase_emoji} {market_phase.title()}",
                        inline=True
                    )
                    
                    # Technical indicators
                    tech_indicators = analysis.get("technical_indicators", {})
                    
                    # Moving averages
                    ma_info = tech_indicators.get("moving_averages", {})
                    ma_5 = ma_info.get("5_period", 0)
                    ma_15 = ma_info.get("15_period", 0)
                    ma_signal = ma_info.get("crossover_signal", "none")
                    
                    ma_emoji = {"bullish": "🟢", "bearish": "🔴", "none": "⚪"}.get(ma_signal, "⚪")
                    embed.add_field(
                        name="📈 Moving Averages",
                        value=f"MA5: ${ma_5:.6f}\nMA15: ${ma_15:.6f}\nSignal: {ma_emoji} {ma_signal.title()}",
                        inline=True
                    )
                    
                    # Trend strength
                    trend_strength = tech_indicators.get("trend_strength", 0)
                    trend_direction = "↗️ Uptrend" if trend_strength > 0.02 else "↘️ Downtrend" if trend_strength < -0.02 else "➡️ Sideways"
                    embed.add_field(
                        name="📊 Trend Analysis",
                        value=f"{trend_direction}\nStrength: {abs(trend_strength):.3f}",
                        inline=True
                    )
                    
                    # Volatility
                    volatility = tech_indicators.get("volatility_signal", "normal")
                    vol_emoji = {"high": "🔥", "elevated": "⚠️", "normal": "✅"}.get(volatility, "❓")
                    embed.add_field(
                        name="💥 Volatility",
                        value=f"{vol_emoji} {volatility.title()}",
                        inline=True
                    )
                    
                    # Pattern signal
                    pattern_signal = tech_indicators.get("pattern_signal", {})
                    signal = pattern_signal.get("signal", "hold")
                    confidence = pattern_signal.get("confidence", 0)
                    strength = pattern_signal.get("strength", "weak")
                    
                    signal_emoji = {"buy": "🟢", "sell": "🔴", "hold": "🟡"}.get(signal, "🟡")
                    embed.add_field(
                        name="🎯 Pattern Signal",
                        value=f"{signal_emoji} {signal.upper()}\nConfidence: {confidence:.2f}\nStrength: {strength.title()}",
                        inline=True
                    )
                    
                    # Support/Resistance
                    sr_info = analysis.get("support_resistance", {})
                    support = sr_info.get("support", 0)
                    resistance = sr_info.get("resistance", 0)
                    near_level = sr_info.get("near_level", False)
                    
                    if support > 0 and resistance > 0:
                        sr_status = "🎯 Near Level" if near_level else "📏 Normal"
                        embed.add_field(
                            name="🔄 Support/Resistance",
                            value=f"Support: ${support:.6f}\nResistance: ${resistance:.6f}\nStatus: {sr_status}",
                            inline=True
                        )
                    
                    # Trading recommendation
                    recommendation = analysis.get("trading_recommendation", {})
                    rec_text = recommendation.get("recommendation", "HOLD")
                    rec_confidence = recommendation.get("confidence", 0)
                    risk_level = recommendation.get("risk_level", "UNKNOWN")
                    signals = recommendation.get("signals", [])
                    
                    rec_emoji = {"STRONG BUY": "🟢🟢", "BUY": "🟢", "HOLD": "🟡", "SELL": "🔴", "STRONG SELL": "🔴🔴"}.get(rec_text, "🟡")
                    embed.add_field(
                        name="💡 Trading Recommendation",
                        value=f"{rec_emoji} **{rec_text}**\nConfidence: {rec_confidence:.2f}\nRisk: {risk_level}",
                        inline=False
                    )
                    
                    if signals:
                        embed.add_field(
                            name="📋 Analysis Signals",
                            value="\n".join(f"• {signal}" for signal in signals[:5]),
                            inline=False
                        )
                    
                    embed.set_footer(text="⚠️ Analysis is for educational purposes. Trade at your own risk!")
                    
                    await interaction.followup.send(embed=embed)
                else:
                    await send_error_response(interaction, "Analysis not available. Advanced simulator may not be initialized.")
            else:
                await send_error_response(interaction, "Advanced analysis not available.")
        else:
            # Show overview of all coins
            embed = create_embed(
                title="📊 Market Analysis Overview",
                description="Use `/crypto analysis <ticker>` for detailed analysis of a specific coin",
                color=0x3498db
            )
            
            coins_list = []
            for coin_ticker in available_tickers[:10]:  # Show first 10
                coin = await CryptoModels.get_coin(coin_ticker)
                if coin:
                    price = coin["current_price"]
                    coins_list.append(f"**{coin_ticker}**: ${price:.6f}")
            
            if coins_list:
                embed.add_field(
                    name="💰 Current Prices",
                    value="\n".join(coins_list),
                    inline=False
                )
            
            embed.add_field(
                name="🎯 Available Analysis",
                value="• Moving Average Crossovers\n• Trend Strength Analysis\n• Support/Resistance Levels\n• Pattern Recognition\n• Trading Recommendations",
                inline=False
            )
            
            embed.add_field(
                name="📋 Available Tickers",
                value=", ".join(available_tickers),
                inline=False
            )
            
            embed.set_footer(text="💡 Skilled traders can use this analysis to improve their trading decisions!")
            
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await send_error_response(interaction, f"Error getting market analysis: {str(e)}")


