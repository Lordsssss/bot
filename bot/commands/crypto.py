import discord
from discord import app_commands, Interaction
from datetime import datetime
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from bot.db.user import get_user
from bot.crypto.models import CryptoModels
from bot.crypto.portfolio import PortfolioManager
from bot.crypto.constants import CRYPTO_COINS, TRANSACTION_FEE
from bot.utils.constants import ALLOWED_CHANNEL_ID
import math

# Prices command
@app_commands.describe()
async def crypto_prices(interaction: Interaction):
    """View current crypto prices"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        coins = await CryptoModels.get_all_coins()
        if not coins:
            await interaction.followup.send("❌ No crypto data available! Market might be initializing...")
            return
        
        # Sort coins by price (highest first)
        coins.sort(key=lambda x: x['current_price'], reverse=True)
        
        embed = discord.Embed(
            title="🪙 Crypto Market Prices",
            description="Current prices for all available cryptocurrencies",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
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
        
        embed.add_field(name="Current Prices", value=price_list, inline=False)
        embed.set_footer(text="Prices update every ~1 minute | Use /crypto chart <ticker> for detailed view")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching prices: {str(e)}")

# Chart command (single crypto)
@app_commands.describe(ticker="Crypto ticker symbol (e.g., DOGE2, MEME)")
async def crypto_chart(interaction: Interaction, ticker: str):
    """View price chart for a specific crypto"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        ticker = ticker.upper()
        
        # Check if coin exists
        coin = await CryptoModels.get_coin(ticker)
        if not coin:
            available_tickers = list(CRYPTO_COINS.keys())
            await interaction.followup.send(f"❌ Crypto {ticker} not found!\nAvailable: {', '.join(available_tickers)}")
            return
        
        # Get price history (last 2 hours)
        price_history = await CryptoModels.get_price_history(ticker, hours=2)
        
        if len(price_history) < 2:
            await interaction.followup.send(f"❌ Not enough price data for {ticker} yet. Try again in a few minutes!")
            return
        
        # Create the chart
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Extract data
        times = [p['timestamp'] for p in price_history]
        prices = [p['price'] for p in price_history]
        
        # Plot the line
        ax.plot(times, prices, color='#00ff00', linewidth=2, marker='o', markersize=3)
        
        # Styling
        ax.set_title(f"{coin['name']} ({ticker}) - Price Chart", fontsize=16, color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel('Price ($)', fontsize=12, color='white')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
        plt.xticks(rotation=45)
        
        # Grid
        ax.grid(True, alpha=0.3, color='gray')
        
        # Current price annotation
        current_price = coin['current_price']
        ax.annotate(f'${current_price:.4f}', 
                   xy=(times[-1], prices[-1]), 
                   xytext=(10, 10), 
                   textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.8),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                   fontsize=12, color='black', weight='bold')
        
        # Calculate price change
        price_change = prices[-1] - prices[0]
        price_change_percent = (price_change / prices[0]) * 100
        
        # Add stats text
        stats_text = f"Current: ${current_price:.4f}\n"
        stats_text += f"Change: {price_change:+.4f} ({price_change_percent:+.2f}%)\n"
        stats_text += f"High: ${max(prices):.4f}\n"
        stats_text += f"Low: ${min(prices):.4f}"
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                fontsize=10, color='white')
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor='#2f3136', dpi=100)
        img_buffer.seek(0)
        plt.close()
        
        # Send the chart
        file = discord.File(img_buffer, filename=f"{ticker}_chart.png")
        
        embed = discord.Embed(
            title=f"📈 {coin['name']} ({ticker})",
            description=f"**Current Price:** ${current_price:.4f}\n"
                       f"**24h Change:** {price_change:+.4f} ({price_change_percent:+.2f}%)\n"
                       f"**Volatility:** {coin['daily_volatility']:.2f}",
            color=0x00ff00 if price_change >= 0 else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        embed.set_image(url=f"attachment://{ticker}_chart.png")
        embed.set_footer(text="Chart shows last 2 hours of trading data")
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error generating chart: {str(e)}")

# Multiple charts command (NEW)
@app_commands.describe(
    tickers="Comma-separated crypto tickers (e.g., 'DOGE2,MEME,BTC') or 'all' for all cryptos"
)
async def crypto_charts(interaction: Interaction, tickers: str):
    """View price charts for multiple cryptos at once"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        # Parse tickers
        if tickers.lower().strip() == 'all':
            target_tickers = list(CRYPTO_COINS.keys())
        else:
            target_tickers = [t.strip().upper() for t in tickers.split(',')]
            # Validate tickers
            invalid_tickers = [t for t in target_tickers if t not in CRYPTO_COINS]
            if invalid_tickers:
                available_tickers = list(CRYPTO_COINS.keys())
                await interaction.followup.send(f"❌ Invalid tickers: {', '.join(invalid_tickers)}\nAvailable: {', '.join(available_tickers)}")
                return
        
        # Limit to prevent overwhelming
        if len(target_tickers) > 6:
            await interaction.followup.send("❌ Maximum 6 charts at once! Use 'all' for all cryptos or specify up to 6 tickers.")
            return
        
        # Collect data for all requested tickers
        chart_data = {}
        valid_tickers = []
        
        for ticker in target_tickers:
            coin = await CryptoModels.get_coin(ticker)
            if not coin:
                continue
                
            price_history = await CryptoModels.get_price_history(ticker, hours=2)
            if len(price_history) < 2:
                continue
                
            chart_data[ticker] = {
                'coin': coin,
                'history': price_history,
                'times': [p['timestamp'] for p in price_history],
                'prices': [p['price'] for p in price_history]
            }
            valid_tickers.append(ticker)
        
        if not valid_tickers:
            await interaction.followup.send("❌ No valid chart data available for the requested cryptos!")
            return
        
        # Create multi-chart layout
        plt.style.use('dark_background')
        
        # Calculate grid layout
        num_charts = len(valid_tickers)
        if num_charts == 1:
            rows, cols = 1, 1
            figsize = (12, 6)
        elif num_charts == 2:
            rows, cols = 1, 2
            figsize = (20, 8)
        elif num_charts <= 4:
            rows, cols = 2, 2
            figsize = (20, 12)
        else:  # 5-6 charts
            rows, cols = 2, 3
            figsize = (24, 12)
        
        fig, axes = plt.subplots(rows, cols, figsize=figsize)
        if num_charts == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]
        else:
            axes = axes.flatten()
        
        # Plot each chart
        colors = ['#00ff00', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#f0932b']
        
        for i, ticker in enumerate(valid_tickers):
            ax = axes[i]
            data = chart_data[ticker]
            color = colors[i % len(colors)]
            
            # Plot the line
            ax.plot(data['times'], data['prices'], color=color, linewidth=2, marker='o', markersize=2)
            
            # Styling
            coin_name = data['coin']['name']
            ax.set_title(f"{coin_name} ({ticker})", fontsize=12, color='white', pad=10)
            ax.set_xlabel('Time', fontsize=10, color='white')
            ax.set_ylabel('Price ($)', fontsize=10, color='white')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
            ax.tick_params(axis='x', rotation=45, labelsize=8)
            ax.tick_params(axis='y', labelsize=8)
            
            # Grid
            ax.grid(True, alpha=0.3, color='gray')
            
            # Current price annotation
            current_price = data['coin']['current_price']
            ax.annotate(f'${current_price:.4f}', 
                       xy=(data['times'][-1], data['prices'][-1]), 
                       xytext=(5, 5), 
                       textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.8),
                       fontsize=8, color='black', weight='bold')
            
            # Calculate price change
            price_change = data['prices'][-1] - data['prices'][0]
            price_change_percent = (price_change / data['prices'][0]) * 100
            
            # Add mini stats
            stats_text = f"${current_price:.4f}\n{price_change_percent:+.1f}%"
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                    fontsize=8, color='white')
        
        # Hide unused subplots
        for i in range(num_charts, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor='#2f3136', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Create summary embed
        embed = discord.Embed(
            title="📊 Multi-Crypto Chart Overview",
            description=f"Price charts for {len(valid_tickers)} cryptocurrencies",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        # Add summary stats
        summary_text = ""
        for ticker in valid_tickers:
            data = chart_data[ticker]
            current_price = data['coin']['current_price']
            price_change = data['prices'][-1] - data['prices'][0]
            price_change_percent = (price_change / data['prices'][0]) * 100
            
            change_emoji = "📈" if price_change >= 0 else "📉"
            summary_text += f"{change_emoji} **{ticker}**: ${current_price:.4f} ({price_change_percent:+.2f}%)\n"
        
        embed.add_field(name="Current Prices & Changes", value=summary_text, inline=False)
        embed.set_footer(text="Charts show last 2 hours of trading data")
        
        # Send the chart
        file = discord.File(img_buffer, filename=f"multi_crypto_chart.png")
        embed.set_image(url="attachment://multi_crypto_chart.png")
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error generating charts: {str(e)}")

# Buy command
@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    amount="Amount of points to spend"
)
async def crypto_buy(interaction: Interaction, ticker: str, amount: float):
    """Buy cryptocurrency with your points"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        ticker = ticker.upper()
        
        # Validate amount
        if amount <= 0:
            await interaction.followup.send("❌ Amount must be positive!")
            return
        
        if amount < 1:
            await interaction.followup.send("❌ Minimum purchase is 1 point!")
            return
        
        # Check if coin exists
        if ticker not in CRYPTO_COINS:
            available_tickers = list(CRYPTO_COINS.keys())
            await interaction.followup.send(f"❌ Crypto {ticker} not found!\nAvailable: {', '.join(available_tickers)}")
            return
        
        # Execute purchase
        result = await PortfolioManager.buy_crypto(user_id, ticker, amount)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Purchase Successful!",
                description=result["message"],
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            details = result["details"]
            embed.add_field(
                name="Transaction Details",
                value=f"**Coins Received:** {details['coins_received']:.6f} {ticker}\n"
                      f"**Price per Coin:** ${details['price_per_coin']:.4f}\n"
                      f"**Total Cost:** {details['total_cost']} points\n"
                      f"**Transaction Fee:** {details['fee']:.2f} points ({TRANSACTION_FEE*100}%)\n"
                      f"**Remaining Points:** {details['remaining_points']:.2f}",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Purchase Failed",
                description=result["message"],
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error processing purchase: {str(e)}")

# Sell command
@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    amount="Amount of crypto to sell"
)
async def crypto_sell(interaction: Interaction, ticker: str, amount: float):
    """Sell cryptocurrency for points"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        ticker = ticker.upper()
        
        # Validate amount
        if amount <= 0:
            await interaction.followup.send("❌ Amount must be positive!")
            return
        
        # Check if coin exists
        if ticker not in CRYPTO_COINS:
            available_tickers = list(CRYPTO_COINS.keys())
            await interaction.followup.send(f"❌ Crypto {ticker} not found!\nAvailable: {', '.join(available_tickers)}")
            return
        
        # Execute sale
        result = await PortfolioManager.sell_crypto(user_id, ticker, amount)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Sale Successful!",
                description=result["message"],
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            details = result["details"]
            embed.add_field(
                name="Transaction Details",
                value=f"**Coins Sold:** {details['coins_sold']} {ticker}\n"
                      f"**Price per Coin:** ${details['price_per_coin']:.4f}\n"
                      f"**Gross Value:** {details['gross_value']:.2f} points\n"
                      f"**Transaction Fee:** {details['fee']:.2f} points ({TRANSACTION_FEE*100}%)\n"
                      f"**Net Received:** {details['net_value']:.2f} points\n"
                      f"**New Balance:** {details['new_points']:.2f} points",
                inline=False
            )
            
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Sale Failed",
                description=result["message"],
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error processing sale: {str(e)}")

# Portfolio command
@app_commands.describe()
async def crypto_portfolio(interaction: Interaction):
    """View your crypto portfolio"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        portfolio_data = await PortfolioManager.get_portfolio_value(user_id)
        
        embed = discord.Embed(
            title=f"🏦 {interaction.user.display_name}'s Crypto Portfolio",
            color=0x00ff00 if portfolio_data["profit_loss"] >= 0 else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        # Portfolio summary
        embed.add_field(
            name="📊 Portfolio Summary",
            value=f"**Total Value:** {portfolio_data['total_value']:.2f} points\n"
                  f"**Total Invested:** {portfolio_data['total_invested']:.2f} points\n"
                  f"**Profit/Loss:** {portfolio_data['profit_loss']:+.2f} points ({portfolio_data['profit_loss_percent']:+.2f}%)",
            inline=False
        )
        
        # Holdings details
        if portfolio_data["holdings"]:
            holdings_text = ""
            for ticker, holding in portfolio_data["holdings"].items():
                holdings_text += f"**{ticker}** ({holding['coin_name']})\n"
                holdings_text += f"  Amount: {holding['amount']:.6f}\n"
                holdings_text += f"  Price: ${holding['current_price']:.4f}\n"
                holdings_text += f"  Value: {holding['value']:.2f} points\n\n"
            
            embed.add_field(
                name="💼 Current Holdings",
                value=holdings_text if holdings_text else "No holdings",
                inline=False
            )
        else:
            embed.add_field(
                name="💼 Current Holdings",
                value="No crypto holdings yet!\nUse `/crypto buy` to start trading.",
                inline=False
            )
        
        # Get user's regular points
        user = await get_user(user_id)
        points = user.get("points", 0)
        embed.add_field(
            name="💰 Available Points",
            value=f"{points:.2f} points",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching portfolio: {str(e)}")

# Leaderboard command
@app_commands.describe()
async def crypto_leaderboard(interaction: Interaction):
    """View crypto trading leaderboard"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        leaderboard = await PortfolioManager.get_leaderboard(limit=10)
        
        if not leaderboard:
            await interaction.followup.send("📊 No crypto traders yet! Be the first to start trading!")
            return
        
        embed = discord.Embed(
            title="🏆 Crypto Trading Leaderboard",
            description="Top traders ranked by profit/loss percentage",
            color=0xffd700,
            timestamp=datetime.utcnow()
        )
        
        leaderboard_text = ""
        for i, trader in enumerate(leaderboard, 1):
            try:
                user = await interaction.client.fetch_user(int(trader["user_id"]))
                username = user.display_name
            except:
                username = f"User {trader['user_id'][:8]}..."
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            leaderboard_text += f"{medal} **{username}**\n"
            leaderboard_text += f"   Value: {trader['total_value']:.2f} pts | "
            leaderboard_text += f"P/L: {trader['profit_loss']:+.2f} ({trader['profit_loss_percent']:+.2f}%)\n\n"
        
        embed.add_field(name="Top Traders", value=leaderboard_text, inline=False)
        embed.set_footer(text="Rankings update with each trade")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching leaderboard: {str(e)}")

# History command
@app_commands.describe()
async def crypto_history(interaction: Interaction):
    """View your recent crypto transactions"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        transactions = await CryptoModels.get_user_transactions(user_id, limit=10)
        
        if not transactions:
            await interaction.followup.send("📋 No crypto transactions yet! Start trading with `/crypto buy`")
            return
        
        embed = discord.Embed(
            title=f"📋 {interaction.user.display_name}'s Transaction History",
            description="Your last 10 crypto transactions",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        history_text = ""
        for tx in transactions:
            action_emoji = "🟢" if tx["type"] == "buy" else "🔴"
            action = tx["type"].upper()
            
            time_str = tx["timestamp"].strftime("%m/%d %H:%M")
            
            history_text += f"{action_emoji} **{action}** {tx['amount']:.6f} {tx['ticker']}\n"
            history_text += f"   Price: ${tx['price']:.4f} | Total: {tx['total_cost']:.2f} pts | {time_str}\n\n"
        
        embed.add_field(name="Recent Transactions", value=history_text, inline=False)
        embed.set_footer(text="Showing last 10 transactions")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching transaction history: {str(e)}")