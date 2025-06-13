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
        
        # Apply volatility (higher volatility = bigger movements) - increased base movement
        volatility_factor = volatility * random_movement * 0.04  # 4% max base movement for more chaos
        
        # Apply hidden trend (increased influence for more dramatic moves)
        # Trend factor: 0.5 = bearish, 1.0 = neutral, 1.5 = bullish
        trend_influence = (self.global_trend - 1.0) * 0.015  # 1.5% max trend influence
        
        # Apply coin-specific trend (increased for more volatility)
        coin_trend_influence = (trend - 1.0) * 0.008  # 0.8% max coin trend
        
        # Time-based scaling (more time = more potential change)
        time_factor = min(time_passed_minutes / 60.0, 2.0)  # Cap at 2 hours worth
        
        # Market momentum (coins tend to continue in the same direction briefly)
        momentum_factor = self.calculate_momentum(coin_data)
        
        # Add random crash/pump factor for unpredictability
        if random.random() < 0.05:  # 5% chance of extreme movement
            crash_pump_factor = (random.random() - 0.5) * 0.30  # Up to ±15% random movement
        else:
            crash_pump_factor = 0.0
        
        # Combine all factors (including new crash/pump factor)
        total_change = (volatility_factor + trend_influence + coin_trend_influence + momentum_factor + crash_pump_factor) * time_factor
        
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
        # Enhanced momentum with more dramatic swings
        base_momentum = (random.random() - 0.5) * 0.025  # ±1.25% base momentum
        
        # Add volatility-based momentum (higher volatility = more momentum)
        volatility_momentum = coin_data.get("daily_volatility", 1.0) * (random.random() - 0.5) * 0.015
        
        return base_momentum + volatility_momentum
    
    def check_market_events(self, ticker: str) -> float:
        """Check if a market event should occur (with 10-minute cooldown)"""
        from datetime import datetime, timedelta
        
        # Check if enough time has passed since last event (10 minutes)
        current_time = datetime.utcnow()
        if (current_time - self.last_event_time).total_seconds() < 600:  # 600 seconds = 10 minutes
            return 0.0
        
        # Random chance for market events (much lower probability)
        for event in MARKET_EVENTS:
            if random.random() < event["probability"]:
                # Event occurred!
                base_impact = event["impact"] * (0.8 + random.random() * 0.4)  # 80-120% of full impact
                
                # Update last event time
                self.last_event_time = current_time
                
                # Handle different event scopes
                if event["scope"] == "single":
                    # Single coin event - affects only the current ticker
                    self.pending_events.append({
                        "message": event["message"],
                        "impact": base_impact,
                        "ticker": ticker,
                        "scope": "single",
                        "affected_coins": [ticker]
                    })
                    return base_impact
                    
                elif event["scope"] == "all":
                    # Market-wide event - affects ALL coins
                    from .constants import CRYPTO_COINS
                    all_tickers = list(CRYPTO_COINS.keys())
                    
                    self.pending_events.append({
                        "message": event["message"],
                        "impact": base_impact,
                        "ticker": ticker,  # Original ticker that triggered it
                        "scope": "all",
                        "affected_coins": all_tickers
                    })
                    return base_impact
                    
                elif event["scope"] == "random_multiple":
                    # Affects 3-6 random coins
                    from .constants import CRYPTO_COINS
                    all_tickers = list(CRYPTO_COINS.keys())
                    num_affected = random.randint(3, min(6, len(all_tickers)))
                    affected_coins = random.sample(all_tickers, num_affected)
                    
                    self.pending_events.append({
                        "message": event["message"],
                        "impact": base_impact,
                        "ticker": ticker,  # Original ticker that triggered it
                        "scope": "random_multiple",
                        "affected_coins": affected_coins
                    })
                    
                    # Return impact only if current ticker is affected
                    return base_impact if ticker in affected_coins else 0.0
                
                # Only allow one event per check to prevent multiple simultaneous events
                break
        
        return 0.0
    
    def generate_daily_volatility(self) -> float:
        """Generate daily volatility for a coin"""
        # Choose volatility category (more chaos, less predictability)
        categories = ["low", "normal", "high", "high", "extreme", "extreme"]  # Favor higher volatility
        category = random.choice(categories)
        min_vol, max_vol = VOLATILITY_RANGES[category]
        
        return random.uniform(min_vol, max_vol)
    
    def calculate_starting_price(self, trend: float) -> float:
        """Calculate starting price with high randomness to prevent predictability"""
        from .constants import MAX_STARTING_PRICE, MIN_STARTING_PRICE
        
        # Much more random starting prices to prevent gaming
        # Remove predictable trend-based pricing
        base_price = random.uniform(MIN_STARTING_PRICE, MAX_STARTING_PRICE)
        
        # Add additional randomness layers
        randomness_1 = random.uniform(0.3, 2.5)  # Wider range
        randomness_2 = random.uniform(0.7, 1.4)  # Second layer
        
        final_price = base_price * randomness_1 * randomness_2
        
        # Ensure within bounds but allow more extreme values
        return max(MIN_STARTING_PRICE * 0.1, min(MAX_STARTING_PRICE * 2.0, final_price))
    
    async def initialize_market(self):
        """Initialize all coins with starting prices and trends"""
        from .constants import CRYPTO_COINS
        
        for ticker, coin_info in CRYPTO_COINS.items():
            # Generate more random coin-specific trend to prevent predictability
            # Wider range and more chaos
            coin_trend = random.uniform(0.3, 1.8)
            
            # Add trend shifts over time to prevent long-term predictability  
            if random.random() < 0.3:  # 30% chance of trend reversal
                coin_trend = 2.1 - coin_trend  # Invert trend
            
            # Generate starting price (now much more random)
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
            
            # Also randomly shift trends to prevent long-term predictability
            if random.random() < 0.4:  # 40% chance of trend shift daily
                current_trend = coin.get("trend", 1.0)
                trend_shift = random.uniform(-0.3, 0.3)
                new_trend = max(0.2, min(1.8, current_trend + trend_shift))
                
                # Update both volatility and trend
                from .models import crypto_coins
                await crypto_coins.update_one(
                    {"ticker": coin["ticker"]},
                    {"$set": {
                        "daily_volatility": new_volatility,
                        "trend": new_trend
                    }}
                )
                
                print(f"Updated {coin['ticker']} volatility to {new_volatility:.2f}, trend to {new_trend:.2f}")
            else:
                # Update volatility only
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