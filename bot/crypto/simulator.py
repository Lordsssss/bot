import random
import math
import os
from datetime import datetime, timedelta
from .constants import MARKET_EVENTS, VOLATILITY_RANGES
from .models import CryptoModels

class MarketSimulator:
    def __init__(self):
        # Get the hidden trend factor from environment
        self.global_trend = float(os.getenv("CRYPTO_TREND_FACTOR", "1.0"))
        self.last_event_time = datetime.utcnow()
    
    def calculate_price_change(self, coin_data: dict, time_passed_minutes: float) -> dict:
        """
        Calculate price change based on:
        - Daily volatility (how much the price moves)
        - Hidden trend factor (long-term direction)
        - Random market movements
        - Market events
        """
        current_price = coin_data["current_price"]
        volatility = coin_data["daily_volatility"]
        trend = coin_data["trend"]
        
        # Base random movement (-1 to 1)
        random_movement = (random.random() - 0.5) * 2
        
        # Apply volatility (higher volatility = bigger movements)
        volatility_factor = volatility * random_movement * 0.02  # 2% max base movement
        
        # Apply hidden trend (subtle influence over time)
        # Trend factor: 0.5 = bearish, 1.0 = neutral, 1.5 = bullish
        trend_influence = (self.global_trend - 1.0) * 0.005  # 0.5% max trend influence
        
        # Apply coin-specific trend
        coin_trend_influence = (trend - 1.0) * 0.003  # 0.3% max coin trend
        
        # Time-based scaling (more time = more potential change)
        time_factor = min(time_passed_minutes / 60.0, 2.0)  # Cap at 2 hours worth
        
        # Market momentum (coins tend to continue in the same direction briefly)
        momentum_factor = self.calculate_momentum(coin_data)
        
        # Combine all factors
        total_change = (volatility_factor + trend_influence + coin_trend_influence + momentum_factor) * time_factor
        
        # Apply market events
        event_impact = self.check_market_events(coin_data["ticker"])
        total_change += event_impact
        
        # Calculate new price
        new_price = current_price * (1 + total_change)
        
        # Ensure price doesn't go negative
        new_price = max(new_price, 0.001)
        
        return {
            "new_price": new_price,
            "change_percent": total_change * 100,
            "change_absolute": new_price - current_price,
            "factors": {
                "volatility": volatility_factor * 100,
                "trend": trend_influence * 100,
                "coin_trend": coin_trend_influence * 100,
                "momentum": momentum_factor * 100,
                "event": event_impact * 100
            }
        }
    
    def calculate_momentum(self, coin_data: dict) -> float:
        """Calculate momentum based on recent price movements"""
        # This would ideally look at recent price history
        # For now, we'll simulate it with a small random factor
        momentum = (random.random() - 0.5) * 0.01  # ±0.5% momentum
        return momentum
    
    def check_market_events(self, ticker: str) -> float:
        """Check if a market event should occur"""
        # Random chance for market events
        total_impact = 0.0
        
        for event in MARKET_EVENTS:
            if random.random() < event["probability"]:
                # Event occurred!
                impact = event["impact"] * (0.5 + random.random() * 0.5)  # 50-100% of full impact
                total_impact += impact
                
                # Record the event (async, so we'll need to handle this separately)
                self.pending_events.append({
                    "message": event["message"],
                    "impact": impact,
                    "ticker": ticker
                })
        
        return total_impact
    
    def generate_daily_volatility(self) -> float:
        """Generate daily volatility for a coin"""
        # Choose volatility category
        categories = ["low", "normal", "normal", "high", "extreme"]  # Normal is more common
        category = random.choice(categories)
        min_vol, max_vol = VOLATILITY_RANGES[category]
        
        return random.uniform(min_vol, max_vol)
    
    def calculate_starting_price(self, trend: float) -> float:
        """Calculate starting price based on trend (lower trend = higher price)"""
        from .constants import MAX_STARTING_PRICE, MIN_STARTING_PRICE
        
        # Invert the trend for starting price
        # Trend 0.5 (bearish) -> higher starting price
        # Trend 1.5 (bullish) -> lower starting price
        inverted_trend = 2.0 - trend
        
        # Scale to price range
        price_range = MAX_STARTING_PRICE - MIN_STARTING_PRICE
        base_price = MIN_STARTING_PRICE + (inverted_trend - 0.5) * price_range / 1.0
        
        # Add some randomness
        randomness = random.uniform(0.8, 1.2)
        final_price = base_price * randomness
        
        # Ensure within bounds
        return max(MIN_STARTING_PRICE, min(MAX_STARTING_PRICE, final_price))
    
    async def initialize_market(self):
        """Initialize all coins with starting prices and trends"""
        from .constants import CRYPTO_COINS
        
        for ticker, coin_info in CRYPTO_COINS.items():
            # Generate coin-specific trend (0.5 to 1.5)
            coin_trend = random.uniform(0.5, 1.5)
            
            # Generate starting price based on trend
            starting_price = self.calculate_starting_price(coin_trend)
            
            # Generate daily volatility
            daily_volatility = self.generate_daily_volatility()
            
            # Initialize in database
            await CryptoModels.initialize_coin(
                ticker=ticker,
                name=coin_info["name"],
                description=coin_info["description"],
                starting_price=starting_price,
                trend=coin_trend,
                volatility=daily_volatility
            )
            
            print(f"Initialized {ticker} ({coin_info['name']}) - Price: ${starting_price:.4f}, Trend: {coin_trend:.2f}, Volatility: {daily_volatility:.2f}")
    
    async def update_daily_volatility(self):
        """Update daily volatility for all coins (called once per day)"""
        coins = await CryptoModels.get_all_coins()
        
        for coin in coins:
            new_volatility = self.generate_daily_volatility()
            
            # Update volatility in database
            from .models import crypto_coins
            await crypto_coins.update_one(
                {"ticker": coin["ticker"]},
                {"$set": {"daily_volatility": new_volatility}}
            )
            
            print(f"Updated {coin['ticker']} volatility to {new_volatility:.2f}")
    
    def __init__(self):
        self.global_trend = float(os.getenv("CRYPTO_TREND_FACTOR", "1.0"))
        self.last_event_time = datetime.utcnow()
        self.pending_events = []  # Store events to be recorded