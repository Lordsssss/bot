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
from bot.utils.constants import ALLOWED_CHANNEL_ID, ADMIN_USER_IDS
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

@app_commands.describe(ticker="Crypto ticker(s) - single (DOGE2), multiple (DOGE2,MEME), or 'all' for all cryptos")
async def crypto_charts(interaction: Interaction, ticker: str):
    """View price chart for one, multiple, or all cryptos (superposed)"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        # Handle 'all' case
        if ticker.lower().strip() == 'all':
            # Get all available cryptos
            all_coins = await CryptoModels.get_all_coins()
            if not all_coins:
                await interaction.followup.send("❌ No crypto data available!")
                return
            tickers = [coin['ticker'] for coin in all_coins]
        else:
            # Parse multiple tickers or single ticker
            tickers = [t.strip().upper() for t in ticker.split(',')]
        
        # Limit to prevent chart overcrowding (max 10 for 'all', unlimited for manual selection)
        if ticker.lower().strip() == 'all':
            tickers = tickers[:10]  # Limit 'all' to 10 most recent
        
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
                await interaction.followup.send("❌ No crypto data available!")
            else:
                available_tickers = list(CRYPTO_COINS.keys())
                await interaction.followup.send(f"❌ No valid cryptos found!\nAvailable: {', '.join(available_tickers)}")
            return
        
        # Create the chart
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(14, 8))  # Slightly larger for multiple lines
        
        # Colors for different lines (expanded palette)
        colors = ['#00ff00', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', 
                 '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
                 '#ff6348', '#2ed573', '#3742fa', '#f368e0', '#feca57']
        
        chart_data = {}
        
        # Get data for each ticker
        for i, t in enumerate(valid_tickers):
            price_history = await CryptoModels.get_price_history(t, hours=2)
            
            if len(price_history) < 2:
                continue
            
            times = [p['timestamp'] for p in price_history]
            prices = [p['price'] for p in price_history]
            
            # For single crypto, show actual prices. For multiple, show percentage change
            if len(valid_tickers) == 1:
                # Single crypto - use actual prices
                plot_values = prices
                ylabel = 'Price ($)'
            else:
                # Multiple cryptos - normalize to percentage change for comparison
                base_price = prices[0]
                plot_values = [(p / base_price - 1) * 100 for p in prices]
                ylabel = 'Price Change (%)'
            
            chart_data[t] = {
                'times': times,
                'prices': prices,
                'plot_values': plot_values,
                'coin': coin_data[t],
                'color': colors[i % len(colors)]
            }
        
        if not chart_data:
            await interaction.followup.send("❌ Not enough price data yet. Try again in a few minutes!")
            return
        
        # Plot all lines superposed
        for t, data in chart_data.items():
            ax.plot(data['times'], data['plot_values'], 
                   color=data['color'], linewidth=2, marker='o' if len(valid_tickers) == 1 else '.', 
                   markersize=3 if len(valid_tickers) == 1 else 1,
                   label=f"{t}" if len(valid_tickers) > 1 else f"{t} ({data['coin']['name']})", 
                   alpha=0.9)
        
        # Dynamic title based on number of cryptos
        if len(valid_tickers) == 1:
            title = f"{coin_data[valid_tickers[0]]['name']} ({valid_tickers[0]}) - Price Chart"
        elif ticker.lower().strip() == 'all':
            title = f"All Crypto Comparison ({len(valid_tickers)} coins)"
        else:
            title = f"Crypto Comparison - {', '.join(valid_tickers)}" if len(', '.join(valid_tickers)) <= 40 else f"Crypto Comparison ({len(valid_tickers)} coins)"
        
        ax.set_title(title, fontsize=16, color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel(ylabel, fontsize=12, color='white')
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
        plt.xticks(rotation=45)
        
        # Grid
        ax.grid(True, alpha=0.3, color='gray')
        
        # Legend and horizontal line (only for multiple cryptos)
        if len(valid_tickers) > 1:
            ax.legend(loc='upper left', fontsize=9, ncol=2 if len(valid_tickers) > 6 else 1)
            ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
        
        # Special annotation for single crypto
        if len(valid_tickers) == 1:
            t = valid_tickers[0]
            data = chart_data[t]
            current_price = data['coin']['current_price']
            
            # Current price annotation
            ax.annotate(f'${current_price:.4f}', 
                       xy=(data['times'][-1], data['prices'][-1]), 
                       xytext=(10, 10), 
                       textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.8),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                       fontsize=12, color='black', weight='bold')
        
        # Stats text box
        if len(valid_tickers) == 1:
            # Detailed stats for single crypto
            t = valid_tickers[0]
            data = chart_data[t]
            current_price = data['coin']['current_price']
            price_change = data['prices'][-1] - data['prices'][0]
            price_change_percent = (price_change / data['prices'][0]) * 100
            
            stats_text = f"Current: ${current_price:.4f}\n"
            stats_text += f"Change: {price_change:+.4f} ({price_change_percent:+.2f}%)\n"
            stats_text += f"High: ${max(data['prices']):.4f}\n"
            stats_text += f"Low: ${min(data['prices']):.4f}\n"
            stats_text += f"Volatility: {data['coin']['daily_volatility']:.2f}"
        else:
            # Summary stats for multiple cryptos
            stats_text = "Current Status:\n"
            # Sort by performance for the stats box
            performance_data = []
            for t, data in chart_data.items():
                current_price = data['coin']['current_price']
                change_pct = data['plot_values'][-1]
                performance_data.append((t, current_price, change_pct))
            
            # Sort by performance (best first)
            performance_data.sort(key=lambda x: x[2], reverse=True)
            
            # Show top performers (limit to 8 lines in stats box)
            for t, current_price, change_pct in performance_data[:8]:
                stats_text += f"{t}: ${current_price:.4f} ({change_pct:+.2f}%)\n"
            
            if len(performance_data) > 8:
                stats_text += f"... and {len(performance_data) - 8} more"
        
        # Position stats box
        box_x = 0.02 if len(valid_tickers) == 1 else 0.98
        box_ha = 'left' if len(valid_tickers) == 1 else 'right'
        
        ax.text(box_x, 0.98, stats_text, transform=ax.transAxes, 
                verticalalignment='top', horizontalalignment=box_ha,
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                fontsize=9, color='white')
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor='#2f3136', dpi=100)
        img_buffer.seek(0)
        plt.close()
        
        # Send the chart
        filename = f"{valid_tickers[0]}_chart.png" if len(valid_tickers) == 1 else "crypto_comparison_chart.png"
        file = discord.File(img_buffer, filename=filename)
        
        # Create embed
        if len(valid_tickers) == 1:
            # Single crypto embed
            t = valid_tickers[0]
            data = chart_data[t]
            current_price = data['coin']['current_price']
            price_change = data['prices'][-1] - data['prices'][0]
            price_change_percent = (price_change / data['prices'][0]) * 100
            
            embed = discord.Embed(
                title=f"📈 {data['coin']['name']} ({t})",
                description=f"**Current Price:** ${current_price:.4f}\n"
                           f"**Change:** {price_change:+.4f} ({price_change_percent:+.2f}%)\n"
                           f"**Volatility:** {data['coin']['daily_volatility']:.2f}",
                color=0x00ff00 if price_change >= 0 else 0xff0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Chart shows last 2 hours of trading data")
        else:
            # Multiple cryptos embed
            embed_color = 0x00ff00  # Default green
            description = f"**Comparing {len(valid_tickers)} cryptocurrencies**\n\n"
            
            # Show top 5 performers in embed
            performance_data = []
            for t, data in chart_data.items():
                current_price = data['coin']['current_price']
                change_pct = data['plot_values'][-1]
                performance_data.append((t, current_price, change_pct))
            
            performance_data.sort(key=lambda x: x[2], reverse=True)
            
            for t, current_price, change_pct in performance_data[:5]:
                description += f"**{t}:** ${current_price:.4f} ({change_pct:+.2f}%)\n"
            
            if len(performance_data) > 5:
                description += f"\n*... and {len(performance_data) - 5} more cryptos*"
            
            embed = discord.Embed(
                title=f"📈 Crypto Comparison Chart",
                description=description,
                color=embed_color,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Chart shows percentage change over last 2 hours | All lines superposed for comparison")
        
        embed.set_image(url=f"attachment://{filename}")
        
        await interaction.followup.send(embed=embed, file=file)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error generating chart: {str(e)}")

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
                value=f"**Coins Received:** {details['coins_received']:.3f} {ticker}\n"
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
                holdings_text += f"  Amount: {holding['amount']:.3f}\n"
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

# Sell All command
@app_commands.describe()
async def crypto_sell_all(interaction: Interaction):
    """Sell all your cryptocurrency holdings at once"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        # Execute sell-all
        result = await PortfolioManager.sell_all_crypto(user_id)
        
        if result["success"]:
            embed = discord.Embed(
                title="✅ Sell All Successful!",
                description=result["message"],
                color=0x00ff00,
                timestamp=datetime.utcnow()
            )
            
            details = result["details"]
            
            # Summary field
            embed.add_field(
                name="💰 Sale Summary",
                value=f"**Total Value:** {details['total_value']:.2f} points\n"
                      f"**Total Fee:** {details['total_fee']:.2f} points\n"
                      f"**Coins Sold:** {details['coins_sold']} different types\n"
                      f"**New Balance:** {details['new_points']:.2f} points",
                inline=False
            )
            
            # Detailed breakdown if not too many coins
            if len(details['sold_holdings']) <= 8:
                breakdown_text = ""
                for holding in details['sold_holdings']:
                    breakdown_text += f"**{holding['ticker']}:** {holding['amount']:.3f} @ ${holding['price']:.4f} = {holding['value']:.2f} pts\n"
                
                embed.add_field(
                    name="📋 Holdings Sold",
                    value=breakdown_text if breakdown_text else "No holdings sold",
                    inline=False
                )
            else:
                embed.add_field(
                    name="📋 Holdings Sold",
                    value=f"Sold {len(details['sold_holdings'])} different cryptocurrencies\n"
                          f"Use `/crypto history` to see detailed transaction list",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Sell All Failed",
                description=result["message"],
                color=0xff0000
            )
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error processing sell all: {str(e)}")

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
            
            history_text += f"{action_emoji} **{action}** {tx['amount']:.3f} {tx['ticker']}\n"
            history_text += f"   Price: ${tx['price']:.4f} | Total: {tx['total_cost']:.2f} pts | {time_str}\n\n"
        
        embed.add_field(name="Recent Transactions", value=history_text, inline=False)
        embed.set_footer(text="Showing last 10 transactions")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error fetching transaction history: {str(e)}")

# Admin Event Trigger command
@app_commands.describe(
    event_type="Type of event to trigger (or 'random' for random event)",
    target_coin="Specific coin to affect (optional, defaults to random)"
)
async def crypto_admin_event(interaction: Interaction, event_type: str, target_coin: str = None):
    """[ADMIN ONLY] Manually trigger a market event"""
    if interaction.channel_id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the designated channel!", ephemeral=True)
        return
    
    # Check if user is admin
    if interaction.user.id not in ADMIN_USER_IDS:
        await interaction.response.send_message("❌ This command is for administrators only!", ephemeral=True)
        return
    
    try:
        await interaction.response.defer()
        
        from bot.crypto.constants import MARKET_EVENTS, CRYPTO_COINS
        import random
        
        # Get available event types for help
        available_events = [
            "hack", "elon", "regulation", "whale", "institutional", 
            "congestion", "partnership", "burn", "fud", "botmalfunction",
            "crash", "moon", "vulnerability", "pump", "diamond", "random"
        ]
        
        event_type = event_type.lower()
        
        # Validate event type
        if event_type not in available_events:
            events_list = ", ".join(available_events)
            await interaction.followup.send(f"❌ Invalid event type! Available: {events_list}")
            return
        
        # Select event
        if event_type == "random":
            selected_event = random.choice(MARKET_EVENTS)
        else:
            # Map short names to event messages
            event_mapping = {
                "hack": "🚨 BREAKING: Major exchange gets hacked!",
                "elon": "📈 Elon Musk tweets about crypto!",
                "regulation": "🏛️ Government announces crypto regulation!",
                "whale": "🐋 Whale alert: Large transaction detected!",
                "institutional": "📊 Institutional investor enters the market!",
                "congestion": "⚡ Network congestion causes delays!",
                "partnership": "🎉 New partnership announced!",
                "burn": "🔥 Token burn event scheduled!",
                "fud": "😱 FUD spreads on social media!",
                "botmalfunction": "🤖 Trading bot malfunction causes chaos!",
                "crash": "💥 Flash crash detected across markets!",
                "moon": "🚀 Surprise moon mission announcement!",
                "vulnerability": "⚠️ Major security vulnerability discovered!",
                "pump": "🎯 Pump and dump scheme exposed!",
                "diamond": "💎 Diamond hands movement trending!"
            }
            
            target_message = event_mapping.get(event_type)
            if not target_message:
                await interaction.followup.send(f"❌ Event mapping not found for: {event_type}")
                return
            
            # Find the matching event
            selected_event = None
            for event in MARKET_EVENTS:
                if target_message in event["message"]:
                    selected_event = event
                    break
            
            if not selected_event:
                await interaction.followup.send(f"❌ Could not find event for: {event_type}")
                return
        
        # Select target coin
        if target_coin:
            target_coin = target_coin.upper()
            if target_coin not in CRYPTO_COINS:
                available_coins = ", ".join(CRYPTO_COINS.keys())
                await interaction.followup.send(f"❌ Invalid coin! Available: {available_coins}")
                return
        else:
            target_coin = random.choice(list(CRYPTO_COINS.keys()))
        
        # Get current coin data
        coin = await CryptoModels.get_coin(target_coin)
        if not coin:
            await interaction.followup.send(f"❌ Could not find coin data for {target_coin}")
            return
        
        # Trigger the event manually
        current_price = coin["current_price"]
        impact = selected_event["impact"]
        new_price = current_price * (1 + impact)
        new_price = max(new_price, 0.001)  # Ensure price doesn't go negative
        
        # Update price in database
        await CryptoModels.update_coin_price(target_coin, new_price, datetime.utcnow())
        
        # Record the event
        await CryptoModels.record_market_event(
            message=f"[ADMIN TRIGGERED] {selected_event['message']}",
            impact=impact,
            affected_coins=[target_coin]
        )
        
        # Send notification to channel (get crypto manager from client)
        if hasattr(interaction.client, 'crypto_manager'):
            fake_event = {
                "message": f"[ADMIN TRIGGERED] {selected_event['message']}",
                "impact": impact,
                "ticker": target_coin
            }
            await interaction.client.crypto_manager.send_event_notification(fake_event, coin)
        
        # Send confirmation to admin
        embed = discord.Embed(
            title="✅ Admin Event Triggered!",
            description=f"Successfully triggered market event",
            color=0x00ff00 if impact > 0 else 0xff0000,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Event Details",
            value=f"**Event:** {selected_event['message']}\n"
                  f"**Target Coin:** {target_coin}\n"
                  f"**Impact:** {impact*100:+.1f}%\n"
                  f"**Old Price:** ${current_price:.4f}\n"
                  f"**New Price:** ${new_price:.4f}",
            inline=False
        )
        
        embed.set_footer(text="Event has been broadcast to the channel")
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error triggering event: {str(e)}", ephemeral=True)