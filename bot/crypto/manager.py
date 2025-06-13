"""
Clean, optimized crypto manager
"""
import asyncio
import random
from datetime import datetime
from .simulator import MarketSimulator
from .models import CryptoModels
from .constants import UPDATE_FREQUENCY_MIN, UPDATE_FREQUENCY_MAX
from bot.utils.discord_helpers import get_impact_color, get_impact_emoji


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
        
        if not self.market_initialized:
            await self._initialize_market()
        
        # Migrate existing portfolios for all-time tracking
        print("🔄 Checking for portfolio migrations...")
        await CryptoModels.migrate_portfolios_for_all_time_tracking()
        print("✅ Portfolio migration complete!")
            
        self.is_running = True
        
        # Start background tasks
        asyncio.create_task(self._price_update_loop())
        asyncio.create_task(self._daily_volatility_update_loop())
        
        print("✅ Crypto Trading System is now running!")
        
    async def stop(self):
        """Stop the crypto trading system"""
        self.is_running = False
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
            await self._send_event_notification(event, affected_coins)
    
    async def _send_event_notification(self, event: dict, affected_coins: list):
        """Send market event notification to Discord"""
        try:
            from bot.utils.constants import ALLOWED_CHANNEL_ID
            import discord
            
            channel = self.client.get_channel(ALLOWED_CHANNEL_ID)
            if not channel:
                return
            
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