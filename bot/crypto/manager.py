"""
Clean, optimized crypto manager with advanced simulator
"""
import asyncio
import random
from datetime import datetime
from .simulator import MarketSimulator
from .advanced_simulator import AdvancedCryptoSimulator
from .models import CryptoModels
from .constants import UPDATE_FREQUENCY_MIN, UPDATE_FREQUENCY_MAX
from bot.utils.discord_helpers import get_impact_color, get_impact_emoji


class CryptoManager:
    def __init__(self, client):
        self.client = client
        self.simulator = MarketSimulator()  # Legacy simulator for fallback
        self.advanced_simulator = AdvancedCryptoSimulator()  # New advanced simulator
        self.use_advanced_mode = True  # Toggle between simulators
        self.is_running = False
        self.market_initialized = False
        self.advanced_initialized = False
        
    async def start(self):
        """Start the crypto trading system"""
        if self.is_running:
            return
            
        print("🚀 Starting Crypto Trading System...")
        
        if not self.market_initialized:
            await self._initialize_market()
        
        # Migrate existing portfolios
        print("🔄 Checking for portfolio migrations...")
        await CryptoModels.migrate_portfolios_for_all_time_tracking()
        await CryptoModels.migrate_portfolios_for_cost_basis()
        print("✅ Portfolio migration complete!")
        
        # Initialize advanced simulator
        if self.use_advanced_mode and not self.advanced_initialized:
            print("🧠 Initializing advanced crypto simulator...")
            try:
                await self.advanced_simulator.initialize()
                self.advanced_initialized = True
                print("🎯 Advanced simulator ready!")
            except Exception as e:
                print(f"⚠️ Advanced simulator failed to initialize: {e}")
                print("📉 Falling back to legacy simulator")
                self.use_advanced_mode = False
            
        self.is_running = True
        
        # Start background tasks
        asyncio.create_task(self._price_update_loop())
        asyncio.create_task(self._daily_volatility_update_loop())
        asyncio.create_task(self._passive_income_loop())
        
        print("✅ Crypto Trading System is now running!")
        
    async def stop(self):
        """Stop the crypto trading system"""
        self.is_running = False
        
        # Cleanup advanced simulator
        if self.advanced_initialized:
            await self.advanced_simulator.cleanup()
            
        print("⏹️ Crypto Trading System stopped.")
        
    async def _initialize_market(self):
        """Initialize the crypto market"""
        try:
            print("📊 Initializing crypto market...")
            
            # Check if already initialized
            existing_coins = await CryptoModels.get_all_coins()
            from .constants import CRYPTO_COINS
            if existing_coins and len(existing_coins) == len(CRYPTO_COINS):
                print("✅ Market already initialized!")
                self.market_initialized = True
                return
                
            await self.simulator.initialize_market()
            self.market_initialized = True
            print("✅ Crypto market initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing market: {e}")
            
    async def _price_update_loop(self):
        """Main loop for updating crypto prices"""
        while self.is_running:
            try:
                await self._update_all_prices()
                
                # Random delay between updates
                delay = random.randint(UPDATE_FREQUENCY_MIN, UPDATE_FREQUENCY_MAX)
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"❌ Error in price update loop: {e}")
                await asyncio.sleep(60)
                
    async def _update_all_prices(self):
        """Update prices for all cryptocurrencies"""
        try:
            if self.use_advanced_mode and self.advanced_initialized:
                # Use advanced simulator
                price_updates = await self.advanced_simulator.update_market_prices()
                
                # Check for executed trigger orders and send notifications
                for update in price_updates:
                    ticker = update["ticker"]
                    new_price = update["price"]
                    change_percent = update.get("change_percent", 0)
                    
                    print(f"🧠 {ticker}: ${new_price:.6f} ({change_percent:+.2f}%)")
                    
                    # Send notifications for executed trigger orders
                    executed_triggers = update.get("executed_triggers", [])
                    if executed_triggers:
                        await self._send_trigger_notifications(executed_triggers)
                
                print(f"🎯 Advanced simulator updated {len(price_updates)} coins")
                
            else:
                # Use legacy simulator
                coins = await CryptoModels.get_all_coins()
                if not coins:
                    return
                    
                current_time = datetime.utcnow()
                
                for coin in coins:
                    # Calculate time since last update
                    last_update = coin.get("last_updated", current_time)
                    if isinstance(last_update, datetime):
                        time_diff = (current_time - last_update).total_seconds() / 60.0
                    else:
                        time_diff = 1.0
                    
                    # Calculate new price
                    price_change_data = self.simulator.calculate_price_change(coin, time_diff)
                    new_price = price_change_data["new_price"]
                    
                    # Update price in database
                    await CryptoModels.update_coin_price(coin["ticker"], new_price, current_time)
                    
                    # Optional: Print price updates
                    change_percent = price_change_data["change_percent"]
                    print(f"📈 {coin['ticker']}: ${new_price:.4f} ({change_percent:+.2f}%)")
                
                # Process any pending events
                await self._process_pending_events(current_time)
                
        except Exception as e:
            print(f"❌ Error updating prices: {e}")
            # Fallback to legacy mode if advanced mode fails
            if self.use_advanced_mode:
                print("⚠️ Switching to legacy simulator due to error")
                self.use_advanced_mode = False
    
    async def _process_pending_events(self, current_time: datetime):
        """Process any pending market events"""
        if not hasattr(self.simulator, 'pending_events') or not self.simulator.pending_events:
            return
        
        events_to_process = self.simulator.pending_events.copy()
        self.simulator.pending_events = []
        
        for event in events_to_process:
            affected_coins = event.get("affected_coins", [])
            
            # Apply event to all affected coins
            for affected_ticker in affected_coins:
                if event["scope"] != "single" or affected_ticker == event["ticker"]:
                    affected_coin = await CryptoModels.get_coin(affected_ticker)
                    if affected_coin:
                        current_price = affected_coin["current_price"]
                        new_price = current_price * (1 + event["impact"])
                        new_price = max(new_price, 0.001)
                        
                        await CryptoModels.update_coin_price(affected_ticker, new_price, current_time)
            
            # Record the event
            await CryptoModels.record_market_event(
                message=event["message"],
                impact=event["impact"],
                affected_coins=affected_coins
            )
            
            # Send Discord notification
            await self.send_event_notification(event, None, affected_coins)
    
    async def send_event_notification(self, event: dict, coin_data: dict = None, affected_coins: list = None):
        """Send market event notification to Discord"""
        try:
            from bot.utils.constants import ALLOWED_CHANNEL_ID
            import discord
            
            channel = self.client.get_channel(ALLOWED_CHANNEL_ID)
            if not channel:
                return
            
            # Use affected_coins from parameter or event
            if affected_coins is None:
                affected_coins = event.get("affected_coins", [])
            
            impact = event["impact"]
            color = get_impact_color(impact)
            impact_emoji = get_impact_emoji(impact)
            
            embed = discord.Embed(
                title=f"{impact_emoji} MARKET EVENT ALERT!",
                description=event["message"],
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Add affected coins info
            if len(affected_coins) == 1:
                embed.add_field(
                    name=f"💰 {affected_coins[0]} Impact",
                    value=f"**Expected Impact:** {impact*100:+.1f}%",
                    inline=False
                )
            elif len(affected_coins) <= 5:
                coins_text = ", ".join(affected_coins)
                embed.add_field(
                    name=f"💰 Affected Coins ({len(affected_coins)})",
                    value=f"**Coins:** {coins_text}\n**Expected Impact:** {impact*100:+.1f}% each",
                    inline=False
                )
            else:
                embed.add_field(
                    name="💰 Market-Wide Impact",
                    value=f"**All {len(affected_coins)} coins affected!**\n**Expected Impact:** {impact*100:+.1f}% across the board",
                    inline=False
                )
            
            # Add trading tips
            if len(affected_coins) > 5:
                if impact < -0.2:
                    footer_text = "💡 MARKET CRASH! Everything is down - buy the dip?"
                elif impact > 0.2:
                    footer_text = "💡 MARKET BOOM! Everything is pumping - time to sell?"
                else:
                    footer_text = "💡 Market-wide movement detected. Trade wisely!"
            else:
                if impact < -0.2:
                    footer_text = "💡 Major crash detected! Could be a buying opportunity..."
                elif impact > 0.2:
                    footer_text = "💡 Big pump happening! Consider taking profits..."
                else:
                    footer_text = "💡 Market movement detected. Trade wisely!"
            
            embed.set_footer(text=footer_text)
            
            await channel.send(embed=embed)
            
            if len(affected_coins) == 1:
                print(f"📢 Event notification sent for {affected_coins[0]}: {event['message']}")
            else:
                print(f"📢 Event notification sent for {len(affected_coins)} coins: {event['message']}")
            
        except Exception as e:
            print(f"❌ Error sending event notification: {e}")
            
    async def _daily_volatility_update_loop(self):
        """Update daily volatility every 24 hours"""
        while self.is_running:
            try:
                await asyncio.sleep(24 * 60 * 60)  # 24 hours
                
                if self.is_running:
                    await self.simulator.update_daily_volatility()
                    print("📊 Daily volatility updated for all coins!")
                    
            except Exception as e:
                print(f"❌ Error in daily volatility update: {e}")
                await asyncio.sleep(60 * 60)  # Wait 1 hour before retrying
    
    async def _passive_income_loop(self):
        """Process Auto-Trader Bot passive income every 6 hours"""
        while self.is_running:
            try:
                await asyncio.sleep(6 * 60 * 60)  # 6 hours
                
                if self.is_running:
                    from bot.items.models import ItemsManager
                    payouts = await ItemsManager.process_passive_income()
                    
                    if payouts:
                        print(f"💰 Processed {len(payouts)} Auto-Trader Bot payouts")
                        for payout in payouts:
                            print(f"   User {payout['user_id']}: +{payout['amount']:.2f} points")
                        
                        # Send Discord notifications
                        await self._send_payout_notifications(payouts)
                    
            except Exception as e:
                print(f"❌ Error in passive income loop: {e}")
                await asyncio.sleep(60 * 60)  # Wait 1 hour before retrying
    
    async def _send_payout_notifications(self, payouts: list):
        """Send Discord notifications for auto-trader payouts"""
        try:
            from bot.utils.constants import ALLOWED_CHANNEL_ID
            from bot.utils.crypto_helpers import format_money
            import discord
            
            channel = self.client.get_channel(ALLOWED_CHANNEL_ID)
            if not channel:
                return
            
            for payout in payouts:
                user_id = payout["user_id"]
                amount = payout["amount"]
                new_balance = payout["balance_after"]
                
                # Get user object for ping
                try:
                    user = await self.client.fetch_user(int(user_id))
                    user_mention = user.mention
                except:
                    user_mention = f"<@{user_id}>"
                
                embed = discord.Embed(
                    title="🤖 Auto-Trader Payout!",
                    description=f"{user_mention} Your auto-trader just earned you {format_money(amount)}!",
                    color=0x00ff00,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="💰 Earnings Summary",
                    value=f"**Earned:** {format_money(amount)}\n**New Balance:** {format_money(new_balance)}",
                    inline=False
                )
                
                embed.set_footer(text="💡 Your auto-trader continues working for you!")
                
                await channel.send(embed=embed)
                print(f"📢 Sent payout notification to user {user_id}")
                
        except Exception as e:
            print(f"❌ Error sending payout notifications: {e}")
    
    async def _send_trigger_notifications(self, executed_triggers: list):
        """Send Discord notifications for executed trigger orders"""
        try:
            from bot.utils.constants import ALLOWED_CHANNEL_ID
            from bot.utils.crypto_helpers import format_money
            import discord
            
            channel = self.client.get_channel(ALLOWED_CHANNEL_ID)
            if not channel:
                return
            
            for trigger_data in executed_triggers:
                order = trigger_data["order"]
                result = trigger_data["result"]
                execution_price = trigger_data["execution_price"]
                actual_gain_percent = trigger_data["actual_gain_percent"]
                amount_sold = trigger_data["amount_sold"]
                
                user_id = order["user_id"]
                ticker = order["ticker"]
                target_gain = order["target_gain_percent"]
                
                # Get user object for ping
                try:
                    user = await self.client.fetch_user(int(user_id))
                    user_mention = user.mention
                except:
                    user_mention = f"<@{user_id}>"
                
                # Determine if target was met or exceeded
                gain_status = "🎯 Target Hit!" if actual_gain_percent >= target_gain else "🚀 Exceeded Target!"
                
                embed = discord.Embed(
                    title="🎯 Trigger Order Executed!",
                    description=f"{user_mention} Your {ticker} trigger order has been executed!",
                    color=0x00ff00 if actual_gain_percent >= 0 else 0xff9900,
                    timestamp=datetime.utcnow()
                )
                
                embed.add_field(
                    name="📊 Execution Details",
                    value=(
                        f"**Crypto:** {ticker}\n"
                        f"**Amount Sold:** {amount_sold:.3f}\n"
                        f"**Execution Price:** {format_money(execution_price)}\n"
                        f"**Total Received:** {format_money(result['details']['net_value'])}"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="📈 Performance",
                    value=(
                        f"**Target Gain:** {target_gain:+.1f}%\n"
                        f"**Actual Gain:** {actual_gain_percent:+.1f}%\n"
                        f"**Status:** {gain_status.split()[1]}"
                    ),
                    inline=True
                )
                
                embed.set_footer(text="💡 Consider setting new trigger orders for future gains!")
                
                await channel.send(embed=embed)
                print(f"📢 Sent trigger notification to user {user_id} for {ticker}")
                
        except Exception as e:
            print(f"❌ Error sending trigger notifications: {e}")
    
    # Public methods for external access
    async def get_market_status(self):
        """Get current market status"""
        try:
            coins = await CryptoModels.get_all_coins()
            
            if not coins:
                return {"status": "offline", "coin_count": 0}
                
            total_market_cap = sum(coin["current_price"] for coin in coins)
            last_update = max(coin.get("last_updated", datetime.min) for coin in coins)
            
            return {
                "status": "online" if self.is_running else "offline",
                "coin_count": len(coins),
                "total_market_cap": total_market_cap,
                "last_update": last_update,
                "coins": coins
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def force_price_update(self):
        """Force an immediate price update"""
        try:
            await self._update_all_prices()
            return True
        except Exception as e:
            print(f"❌ Error in force price update: {e}")
            return False
    
    async def reset_market(self):
        """Reset the entire market (admin function)"""
        try:
            print("🔄 Resetting crypto market...")
            
            from .models import crypto_coins, crypto_prices, crypto_portfolios, crypto_transactions, crypto_events
            
            await crypto_coins.delete_many({})
            await crypto_prices.delete_many({})
            await crypto_portfolios.delete_many({})
            await crypto_transactions.delete_many({})
            await crypto_events.delete_many({})
            
            self.market_initialized = False
            await self._initialize_market()
            
            print("✅ Market reset complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting market: {e}")
            return False