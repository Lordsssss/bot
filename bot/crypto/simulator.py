"""
Clean, optimized market simulator with explosive price movements
"""
import random
import os
from datetime import datetime
from .constants import MARKET_EVENTS, VOLATILITY_RANGES
from .models import CryptoModels


class MarketSimulator:
    def __init__(self):
        self.last_event_time = datetime.utcnow()
        self.pending_events = []
    
    def calculate_price_change(self, coin_data: dict, time_passed_minutes: float) -> dict:
        """Calculate EXPLOSIVE price changes - massive jumps up or down!"""
        current_price = coin_data["current_price"]
        volatility = coin_data["daily_volatility"]
        
        # EXPLOSIVE MOVEMENT SYSTEM
        direction = 1 if random.random() > 0.5 else -1
        base_movement = random.uniform(0.10, 0.40)  # 10-40% base movement
        volatility_multiplier = volatility / 10.0
        explosive_movement = base_movement * (1 + volatility_multiplier)
        total_change = direction * explosive_movement
        
        # MEGA CHAOS FACTOR - 15% chance of insane movement
        if random.random() < 0.15:
            mega_direction = 1 if random.random() > 0.5 else -1
            mega_movement = random.uniform(0.50, 1.50)  # 50-150% mega movement!
            total_change = mega_direction * mega_movement
        
        # Apply market events
        event_impact = self.check_market_events(coin_data["ticker"])
        total_change += event_impact
        
        # Calculate new price
        new_price = current_price * (1 + total_change)
        new_price = max(new_price, 0.0001)  # Prevent negative prices
        
        return {
            "new_price": new_price,
            "change_percent": total_change * 100,
            "change_absolute": new_price - current_price
        }
    
    def check_market_events(self, ticker: str) -> float:
        """Check if a market event should occur (with 10-minute cooldown)"""
        current_time = datetime.utcnow()
        if (current_time - self.last_event_time).total_seconds() < 600:  # 10 minutes
            return 0.0
        
        for event in MARKET_EVENTS:
            if random.random() < event["probability"]:
                base_impact = event["impact"] * random.uniform(0.8, 1.2)  # 80-120% variance
                self.last_event_time = current_time
                
                # Determine affected coins based on event scope
                if event["scope"] == "all":
                    from .constants import CRYPTO_COINS
                    affected_coins = list(CRYPTO_COINS.keys())
                elif event["scope"] == "random_multiple":
                    from .constants import CRYPTO_COINS
                    all_tickers = list(CRYPTO_COINS.keys())
                    num_affected = random.randint(3, min(6, len(all_tickers)))
                    affected_coins = random.sample(all_tickers, num_affected)
                else:  # single
                    affected_coins = [ticker]
                
                self.pending_events.append({
                    "message": event["message"],
                    "impact": base_impact,
                    "ticker": ticker,
                    "scope": event["scope"],
                    "affected_coins": affected_coins
                })
                
                return base_impact if ticker in affected_coins else 0.0
        
        return 0.0
    
    def generate_daily_volatility(self) -> float:
        """Generate EXTREME volatility for maximum chaos"""
        categories = ["high", "extreme", "extreme", "extreme"]  # Heavily favor extreme
        category = random.choice(categories)
        min_vol, max_vol = VOLATILITY_RANGES[category]
        return random.uniform(min_vol, max_vol)
    
    def calculate_starting_price(self) -> float:
        """Calculate random starting price"""
        from .constants import MAX_STARTING_PRICE, MIN_STARTING_PRICE
        
        base_price = random.uniform(MIN_STARTING_PRICE, MAX_STARTING_PRICE)
        randomness = random.uniform(0.3, 2.5) * random.uniform(0.7, 1.4)
        final_price = base_price * randomness
        
        return max(MIN_STARTING_PRICE * 0.1, min(MAX_STARTING_PRICE * 2.0, final_price))
    
    async def initialize_market(self):
        """Initialize all coins with starting prices and trends"""
        from .constants import CRYPTO_COINS
        
        for ticker, coin_info in CRYPTO_COINS.items():
            coin_trend = random.uniform(0.3, 1.8)
            if random.random() < 0.3:  # 30% chance of trend reversal
                coin_trend = 2.1 - coin_trend
            
            starting_price = self.calculate_starting_price()
            daily_volatility = self.generate_daily_volatility()
            
            await CryptoModels.initialize_coin(
                ticker=ticker,
                name=coin_info["name"],
                description=coin_info["description"],
                starting_price=starting_price,
                trend=coin_trend,
                volatility=daily_volatility
            )
            
            print(f"Initialized {ticker} - Price: ${starting_price:.4f}, Volatility: {daily_volatility:.2f}")
    
    async def update_daily_volatility(self):
        """Update daily volatility for all coins"""
        coins = await CryptoModels.get_all_coins()
        
        for coin in coins:
            new_volatility = self.generate_daily_volatility()
            
            update_data = {"daily_volatility": new_volatility}
            
            # 40% chance of trend shift to prevent predictability
            if random.random() < 0.4:
                current_trend = coin.get("trend", 1.0)
                trend_shift = random.uniform(-0.3, 0.3)
                new_trend = max(0.2, min(1.8, current_trend + trend_shift))
                update_data["trend"] = new_trend
                print(f"Updated {coin['ticker']} volatility: {new_volatility:.2f}, trend: {new_trend:.2f}")
            else:
                print(f"Updated {coin['ticker']} volatility: {new_volatility:.2f}")
            
            from .models import crypto_coins
            await crypto_coins.update_one(
                {"ticker": coin["ticker"]},
                {"$set": update_data}
            )