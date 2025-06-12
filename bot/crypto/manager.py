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
                    for event in self.simulator.pending_events:
                        if event["ticker"] == coin["ticker"]:
                            await CryptoModels.record_market_event(
                                message=event["message"],
                                impact=event["impact"],
                                affected_coins=[coin["ticker"]]
                            )
                    
                    # Clear processed events
                    self.simulator.pending_events = []
                
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