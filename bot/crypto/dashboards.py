import discord
from discord.ext import commands
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from .models import get_crypto_portfolio, get_crypto_prices, get_crypto_transactions, get_crypto_trigger_orders
from .chart_generator import generate_price_chart
from .constants import CRYPTO_COINS
from .dashboard_helpers import (
    execute_buy_crypto, execute_sell_crypto, calculate_portfolio_value,
    get_portfolio_pl, format_leaderboard_embed
)


class BaseCryptoDashboard(discord.ui.View):
    """Base class for crypto dashboards with user authorization"""
    
    def __init__(self, authorized_user_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.authorized_user_id = authorized_user_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the user is authorized to use this dashboard"""
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(
                "❌ Only the user who opened this dashboard can interact with it.",
                ephemeral=True
            )
            return False
        return True
    
    async def on_timeout(self):
        """Disable all buttons when the view times out"""
        for item in self.children:
            item.disabled = True


class PortfolioDashboard(BaseCryptoDashboard):
    """Main portfolio dashboard with quick trading"""
    
    def __init__(self, authorized_user_id: int, ctx, timeout: float = 300):
        super().__init__(authorized_user_id, timeout)
        self.ctx = ctx
        self.selected_coin = None
    
    @discord.ui.select(
        placeholder="Select a cryptocurrency to trade",
        options=[
            discord.SelectOption(label=f"{coin_data['name']} ({ticker})", value=ticker)
            for ticker, coin_data in CRYPTO_COINS.items()
        ]
    )
    async def select_coin(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_coin = select.values[0]
        coin_name = CRYPTO_COINS[self.selected_coin]['name']
        await interaction.response.send_message(
            f"💰 Selected **{coin_name} ({self.selected_coin})** for trading",
            ephemeral=True
        )
    
    @discord.ui.button(label="🔄 Refresh Portfolio", style=discord.ButtonStyle.primary)
    async def refresh_portfolio(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._get_portfolio_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="💸 Buy All Balance", style=discord.ButtonStyle.green)
    async def buy_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_coin:
            await interaction.response.send_message(
                "❌ Please select a cryptocurrency first using the dropdown above.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Execute buy with all available balance
        result = await execute_buy_crypto(self.ctx, self.selected_coin, "all")
        
        if result["success"]:
            # Refresh the dashboard
            embed = await self._get_portfolio_embed()
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
    
    @discord.ui.button(label="💰 Sell All Holdings", style=discord.ButtonStyle.red)
    async def sell_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_coin:
            await interaction.response.send_message(
                "❌ Please select a cryptocurrency first using the dropdown above.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Execute sell all holdings of selected coin
        result = await execute_sell_crypto(self.ctx, self.selected_coin, "all")
        
        if result["success"]:
            # Refresh the dashboard
            embed = await self._get_portfolio_embed()
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
    
    @discord.ui.button(label="📊 Market Dashboard", style=discord.ButtonStyle.secondary)
    async def market_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        market_view = MarketDashboard(self.authorized_user_id, self.ctx)
        embed = await market_view._get_market_embed()
        await interaction.response.edit_message(embed=embed, view=market_view)
    
    @discord.ui.button(label="⚡ Trading Dashboard", style=discord.ButtonStyle.secondary)
    async def trading_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        trading_view = TradingDashboard(self.authorized_user_id, self.ctx)
        embed = await trading_view._get_trading_embed()
        await interaction.response.edit_message(embed=embed, view=trading_view)
    
    async def _get_portfolio_embed(self) -> discord.Embed:
        """Generate portfolio embed"""
        portfolio = get_crypto_portfolio(self.authorized_user_id)
        prices = get_crypto_prices()
        
        embed = discord.Embed(
            title="🏦 Crypto Portfolio Dashboard",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        if not portfolio:
            embed.description = "📈 Your portfolio is empty. Start trading to see your holdings here!"
            embed.add_field(
                name="💡 Quick Start",
                value="1. Select a coin from the dropdown\n2. Use **Buy All Balance** to invest\n3. Watch your portfolio grow!",
                inline=False
            )
            return embed
        
        total_value, total_cost, total_pl, total_pl_percent = calculate_portfolio_value(portfolio, prices)
        
        # Portfolio summary
        embed.add_field(
            name="💼 Portfolio Summary",
            value=f"**Total Value:** 🪙 {total_value:,.0f}\n"
                  f"**Total Cost:** 🪙 {total_cost:,.0f}\n"
                  f"**P/L:** {'🟢' if total_pl >= 0 else '🔴'} {total_pl:+,.0f} ({total_pl_percent:+.1f}%)",
            inline=False
        )
        
        # Holdings
        holdings_text = ""
        for ticker, data in portfolio.items():
            if data['amount'] > 0:
                current_price = prices.get(ticker, 0)
                value = data['amount'] * current_price
                cost = data['cost_basis']
                pl = value - cost
                pl_percent = (pl / cost * 100) if cost > 0 else 0
                
                coin_name = CRYPTO_COINS.get(ticker, {}).get('name', ticker)
                holdings_text += f"**{coin_name}** ({ticker})\n"
                holdings_text += f"├ Amount: {data['amount']:,.2f}\n"
                holdings_text += f"├ Value: 🪙 {value:,.0f}\n"
                holdings_text += f"└ P/L: {'🟢' if pl >= 0 else '🔴'} {pl:+,.0f} ({pl_percent:+.1f}%)\n\n"
        
        if holdings_text:
            embed.add_field(name="📈 Current Holdings", value=holdings_text, inline=False)
        
        # Recent transactions
        transactions = get_crypto_transactions(self.authorized_user_id, limit=3)
        if transactions:
            tx_text = ""
            for tx in transactions:
                action_emoji = "🟢" if tx['action'] == 'buy' else "🔴"
                coin_name = CRYPTO_COINS.get(tx['ticker'], {}).get('name', tx['ticker'])
                tx_text += f"{action_emoji} {tx['action'].upper()} {tx['amount']:,.2f} {coin_name}\n"
            embed.add_field(name="📝 Recent Transactions", value=tx_text, inline=False)
        
        embed.set_footer(text="💡 Select a coin and use Buy All/Sell All for quick trading")
        return embed


class MarketDashboard(BaseCryptoDashboard):
    """Market information dashboard"""
    
    def __init__(self, authorized_user_id: int, ctx, timeout: float = 300):
        super().__init__(authorized_user_id, timeout)
        self.ctx = ctx
        self.selected_chart_coin = "all"
    
    @discord.ui.select(
        placeholder="Select cryptocurrency for chart",
        options=[
            discord.SelectOption(label="All Coins", value="all", emoji="📊"),
            *[
                discord.SelectOption(label=f"{coin_data['name']} ({ticker})", value=ticker)
                for ticker, coin_data in CRYPTO_COINS.items()
            ]
        ]
    )
    async def select_chart_coin(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected_chart_coin = select.values[0]
        await interaction.response.defer()
        
        # Generate and send chart
        chart_file = await generate_price_chart(self.selected_chart_coin, "24h")
        if chart_file:
            await interaction.followup.send(file=chart_file, ephemeral=True)
        else:
            await interaction.followup.send("❌ Failed to generate chart", ephemeral=True)
    
    @discord.ui.button(label="🔄 Refresh Prices", style=discord.ButtonStyle.primary)
    async def refresh_prices(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._get_market_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🏆 Leaderboard", style=discord.ButtonStyle.green)
    async def show_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await format_leaderboard_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🏦 Portfolio Dashboard", style=discord.ButtonStyle.secondary)
    async def portfolio_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        portfolio_view = PortfolioDashboard(self.authorized_user_id, self.ctx)
        embed = await portfolio_view._get_portfolio_embed()
        await interaction.response.edit_message(embed=embed, view=portfolio_view)
    
    @discord.ui.button(label="⚡ Trading Dashboard", style=discord.ButtonStyle.secondary)
    async def trading_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        trading_view = TradingDashboard(self.authorized_user_id, self.ctx)
        embed = await trading_view._get_trading_embed()
        await interaction.response.edit_message(embed=embed, view=trading_view)
    
    async def _get_market_embed(self) -> discord.Embed:
        """Generate market information embed"""
        prices = get_crypto_prices()
        
        embed = discord.Embed(
            title="📊 Crypto Market Dashboard",
            color=0x0099ff,
            timestamp=datetime.utcnow()
        )
        
        if not prices:
            embed.description = "❌ No price data available"
            return embed
        
        # Current prices
        prices_text = ""
        for ticker, price in prices.items():
            coin_data = CRYPTO_COINS.get(ticker, {})
            name = coin_data.get('name', ticker)
            emoji = coin_data.get('emoji', '🪙')
            prices_text += f"{emoji} **{name}** ({ticker}): 🪙 {price:,.2f}\n"
        
        embed.add_field(name="💰 Current Prices", value=prices_text, inline=False)
        embed.add_field(
            name="📈 Charts",
            value="Select a cryptocurrency from the dropdown above to view its price chart",
            inline=False
        )
        
        embed.set_footer(text="💡 Prices update every 15-30 seconds")
        return embed


class TradingDashboard(BaseCryptoDashboard):
    """Advanced trading dashboard with trigger orders"""
    
    def __init__(self, authorized_user_id: int, ctx, timeout: float = 300):
        super().__init__(authorized_user_id, timeout)
        self.ctx = ctx
    
    @discord.ui.button(label="🔄 Refresh Orders", style=discord.ButtonStyle.primary)
    async def refresh_orders(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._get_trading_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="📝 Transaction History", style=discord.ButtonStyle.green)
    async def show_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        transactions = get_crypto_transactions(self.authorized_user_id, limit=10)
        
        embed = discord.Embed(
            title="📝 Transaction History",
            color=0x00ff00,
            timestamp=datetime.utcnow()
        )
        
        if not transactions:
            embed.description = "No transactions found"
        else:
            history_text = ""
            for tx in transactions:
                action_emoji = "🟢" if tx['action'] == 'buy' else "🔴"
                coin_name = CRYPTO_COINS.get(tx['ticker'], {}).get('name', tx['ticker'])
                timestamp = tx.get('timestamp', 'Unknown')
                history_text += f"{action_emoji} **{tx['action'].upper()}** {tx['amount']:,.2f} {coin_name}\n"
                history_text += f"├ Price: 🪙 {tx.get('price', 0):,.2f}\n"
                history_text += f"└ Time: {timestamp}\n\n"
            
            embed.description = history_text
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🏦 Portfolio Dashboard", style=discord.ButtonStyle.secondary)
    async def portfolio_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        portfolio_view = PortfolioDashboard(self.authorized_user_id, self.ctx)
        embed = await portfolio_view._get_portfolio_embed()
        await interaction.response.edit_message(embed=embed, view=portfolio_view)
    
    @discord.ui.button(label="📊 Market Dashboard", style=discord.ButtonStyle.secondary)
    async def market_dashboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        market_view = MarketDashboard(self.authorized_user_id, self.ctx)
        embed = await market_view._get_market_embed()
        await interaction.response.edit_message(embed=embed, view=market_view)
    
    async def _get_trading_embed(self) -> discord.Embed:
        """Generate trading dashboard embed"""
        trigger_orders = get_crypto_trigger_orders(self.authorized_user_id)
        
        embed = discord.Embed(
            title="⚡ Advanced Trading Dashboard",
            color=0xff6600,
            timestamp=datetime.utcnow()
        )
        
        # Active trigger orders
        if not trigger_orders:
            embed.add_field(
                name="📋 Active Trigger Orders",
                value="No active trigger orders",
                inline=False
            )
        else:
            orders_text = ""
            for i, order in enumerate(trigger_orders, 1):
                coin_name = CRYPTO_COINS.get(order['ticker'], {}).get('name', order['ticker'])
                orders_text += f"**{i}.** {coin_name} ({order['ticker']})\n"
                orders_text += f"├ Target Gain: {order['target_gain_percent']:+.1f}%\n"
                orders_text += f"└ Amount: {order['amount']:,.2f}\n\n"
            
            embed.add_field(name="📋 Active Trigger Orders", value=orders_text, inline=False)
        
        # Quick info
        embed.add_field(
            name="💡 Advanced Trading",
            value="• Use **/crypto trigger-set** to create automatic sell orders\n"
                  "• Use **/crypto trigger-cancel** to remove orders\n"
                  "• View transaction history with the button above",
            inline=False
        )
        
        embed.set_footer(text="💡 Trigger orders execute automatically when price targets are reached")
        return embed