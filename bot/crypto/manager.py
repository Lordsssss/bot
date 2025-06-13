import asyncio
import random
from datetime import datetime, timedelta
from .simulator import MarketSimulator
from .models import CryptoModels
from .constants import UPDATE_FREQUENCY_MIN, UPDATE_FREQUENCY_MAX, CRYPTO_COINS

class CryptoManager:
    def __init__(self, client):
        self.client = client
        self.simulator = MarketSimulator()
        self.is_running = False
        self.market_initialized = False
        
    async def start(self):
        """Start the crypto trading system"""
        if self.is_running:
            return
            
        print("🚀 Starting Crypto Trading System...")
        
        # Initialize market if not done
        if not self.market_initialized:
            await self.initialize_market()
        
        # Migrate existing portfolios for all-time tracking
        print("🔄 Checking for portfolio migrations...")
        await CryptoModels.migrate_portfolios_for_all_time_tracking()
        print("✅ Portfolio migration complete!")
            
        self.is_running = True
        
        # Start background tasks
        asyncio.create_task(self.price_update_loop())
        asyncio.create_task(self.daily_volatility_update_loop())
        
        print("✅ Crypto Trading System is now running!")
        
    async def stop(self):
        """Stop the crypto trading system"""
        self.is_running = False
        print("⏹️ Crypto Trading System stopped.")
        
    async def initialize_market(self):
        """Initialize the crypto market with starting data"""
        try:
            print("📊 Initializing crypto market...")
            
            # Check if market is already initialized
            existing_coins = await CryptoModels.get_all_coins()
            if existing_coins and len(existing_coins) == len(CRYPTO_COINS):
                print("✅ Market already initialized!")
                self.market_initialized = True
                return
                
            # Initialize market
            await self.simulator.initialize_market()
            self.market_initialized = True
            
            print("✅ Crypto market initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing market: {e}")
            
    async def price_update_loop(self):
        """Main loop for updating crypto prices"""
        while self.is_running:
            try:
                await self.update_all_prices()
                
                # Random delay between updates (45-75 seconds)
                delay = random.randint(UPDATE_FREQUENCY_MIN, UPDATE_FREQUENCY_MAX)
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(f"❌ Error in price update loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
                
    async def update_all_prices(self):
        """Update prices for all cryptocurrencies"""
        try:
            coins = await CryptoModels.get_all_coins()
            
            if not coins:
                print("⚠️ No coins found for price update!")
                return
                
            current_time = datetime.utcnow()
            
            for coin in coins:
                # Calculate time since last update
                last_update = coin.get("last_updated", current_time)
                if isinstance(last_update, datetime):
                    time_diff = (current_time - last_update).total_seconds() / 60.0  # minutes
                else:
                    time_diff = 1.0  # Default to 1 minute
                
                # Calculate new price
                price_change_data = self.simulator.calculate_price_change(coin, time_diff)
                new_price = price_change_data["new_price"]
                
                # Update price in database
                await CryptoModels.update_coin_price(coin["ticker"], new_price, current_time)
                
                # Process any pending events
                if hasattr(self.simulator, 'pending_events') and self.simulator.pending_events:
                    events_to_process = self.simulator.pending_events.copy()
                    self.simulator.pending_events = []  # Clear immediately to prevent duplication
                    
                    for event in events_to_process:
                        # Handle multi-coin events
                        affected_coins = event.get("affected_coins", [coin["ticker"]])
                        
                        # Apply the event to all affected coins
                        for affected_ticker in affected_coins:
                            if event["scope"] != "single" or affected_ticker == coin["ticker"]:
                                # Get the affected coin data
                                affected_coin = await CryptoModels.get_coin(affected_ticker)
                                if affected_coin:
                                    # Calculate new price for this coin
                                    current_price = affected_coin["current_price"]
                                    new_price = current_price * (1 + event["impact"])
                                    new_price = max(new_price, 0.001)  # Ensure price doesn't go negative
                                    
                                    # Update price in database
                                    await CryptoModels.update_coin_price(affected_ticker, new_price, current_time)
                        
                        # Record the event once (not per coin)
                        await CryptoModels.record_market_event(
                            message=event["message"],
                            impact=event["impact"],
                            affected_coins=affected_coins
                        )
                        
                        # Send event notification to Discord channel (once per event)
                        await self.send_event_notification(event, coin, affected_coins)
                
                # Optional: Print price updates (remove in production)
                change_percent = price_change_data["change_percent"]
                print(f"📈 {coin['ticker']}: ${new_price:.4f} ({change_percent:+.2f}%)")
                
        except Exception as e:
            print(f"❌ Error updating prices: {e}")
            
    async def daily_volatility_update_loop(self):
        """Update daily volatility every 24 hours"""
        while self.is_running:
            try:
                # Wait 24 hours
                await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds
                
                if self.is_running:
                    await self.simulator.update_daily_volatility()
                    print("📊 Daily volatility updated for all coins!")
                    
            except Exception as e:
                print(f"❌ Error in daily volatility update: {e}")
                await asyncio.sleep(60 * 60)  # Wait 1 hour before retrying
                
    async def get_market_status(self):
        """Get current market status"""
        try:
            coins = await CryptoModels.get_all_coins()
            
            if not coins:
                return {
                    "status": "offline",
                    "coin_count": 0,
                    "total_market_cap": 0,
                    "last_update": None
                }
                
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
            print(f"❌ Error getting market status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    async def force_price_update(self):
        """Force an immediate price update for all coins"""
        try:
            await self.update_all_prices()
            return True
        except Exception as e:
            print(f"❌ Error in force price update: {e}")
            return False
            
    async def reset_market(self):
        """Reset the entire market (admin function)"""
        try:
            print("🔄 Resetting crypto market...")
            
            # Clear all existing data
            from .models import crypto_coins, crypto_prices, crypto_portfolios, crypto_transactions, crypto_events
            
            await crypto_coins.delete_many({})
            await crypto_prices.delete_many({})
            await crypto_portfolios.delete_many({})
            await crypto_transactions.delete_many({})
            await crypto_events.delete_many({})
            
            # Reinitialize
            self.market_initialized = False
            await self.initialize_market()
            
            print("✅ Market reset complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting market: {e}")
            return False
            
    async def get_recent_events(self, hours: int = 1):
        """Get recent market events"""
        try:
            return await CryptoModels.get_recent_events(hours)
        except Exception as e:
            print(f"❌ Error getting recent events: {e}")
            return []
    
    async def send_event_notification(self, event, coin, affected_coins=None):
        """Send market event notification to Discord channel"""
        try:
            from bot.utils.constants import ALLOWED_CHANNEL_ID
            import discord
            
            # Get the channel
            channel = self.client.get_channel(ALLOWED_CHANNEL_ID)
            if not channel:
                print(f"⚠️ Channel {ALLOWED_CHANNEL_ID} not found for event notification")
                return
            
            # Determine impact color and emoji
            impact = event["impact"]
            if impact > 0.3:
                color = 0x00ff00  # Bright green for big pumps
                impact_emoji = "📈🚀"
            elif impact > 0.1:
                color = 0x90EE90  # Light green for moderate pumps
                impact_emoji = "📈"
            elif impact > -0.1:
                color = 0xffff00  # Yellow for neutral
                impact_emoji = "➡️"
            elif impact > -0.3:
                color = 0xffa500  # Orange for moderate dumps
                impact_emoji = "📉"
            else:
                color = 0xff0000  # Red for big crashes
                impact_emoji = "📉💥"
            
            # Create embed
            embed = discord.Embed(
                title=f"{impact_emoji} MARKET EVENT ALERT!",
                description=event["message"],
                color=color,
                timestamp=datetime.utcnow()
            )
            
            # Add affected coin info based on scope
            if not affected_coins:
                affected_coins = [coin['ticker']]
            
            if len(affected_coins) == 1:
                # Single coin impact
                current_price = coin["current_price"]
                embed.add_field(
                    name=f"💰 {coin['ticker']} Impact",
                    value=f"**Current Price:** ${current_price:.4f}\n"
                          f"**Expected Impact:** {impact*100:+.1f}%\n"
                          f"**Coin:** {coin['name']}",
                    inline=False
                )
            elif len(affected_coins) <= 5:
                # Multiple coins - show list
                coins_text = ", ".join(affected_coins)
                embed.add_field(
                    name=f"💰 Affected Coins ({len(affected_coins)})",
                    value=f"**Coins:** {coins_text}\n"
                          f"**Expected Impact:** {impact*100:+.1f}% each",
                    inline=False
                )
            else:
                # Many coins affected
                embed.add_field(
                    name=f"💰 Market-Wide Impact",
                    value=f"**All {len(affected_coins)} coins affected!**\n"
                          f"**Expected Impact:** {impact*100:+.1f}% across the board",
                    inline=False
                )
            
            # Add footer with trading tip based on scope and impact
            if len(affected_coins) > 5:
                if impact < -0.2:
                    embed.set_footer(text="💡 MARKET CRASH! Everything is down - buy the dip?")
                elif impact > 0.2:
                    embed.set_footer(text="💡 MARKET BOOM! Everything is pumping - time to sell?")
                else:
                    embed.set_footer(text="💡 Market-wide movement detected. Trade wisely!")
            else:
                if impact < -0.2:
                    embed.set_footer(text="💡 Major crash detected! Could be a buying opportunity...")
                elif impact > 0.2:
                    embed.set_footer(text="💡 Big pump happening! Consider taking profits...")
                else:
                    embed.set_footer(text="💡 Market movement detected. Trade wisely!")
            
            # Send the message
            await channel.send(embed=embed)
            if len(affected_coins) == 1:
                print(f"📢 Event notification sent for {affected_coins[0]}: {event['message']}")
            else:
                print(f"📢 Event notification sent for {len(affected_coins)} coins: {event['message']}")
            
        except Exception as e:
            print(f"❌ Error sending event notification: {e}")