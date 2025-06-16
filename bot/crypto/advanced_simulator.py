"""
Advanced crypto simulator with real pattern integration and skill-based mechanics
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .data_fetcher import CryptoDataFetcher, PatternAnalyzer
from .win_rate_balancer import WinRateBalancer
from .models import CryptoModels
from .constants import CRYPTO_COINS, MINIMUM_PRICE_FLOOR
from .trigger_orders import check_and_execute_triggers
import math

class AdvancedCryptoSimulator:
    """Advanced simulator with real crypto patterns and skill-based mechanics"""
    
    def __init__(self):
        self.data_fetcher = CryptoDataFetcher()
        self.pattern_analyzer = PatternAnalyzer()
        self.win_rate_balancer = WinRateBalancer()
        self.pattern_cache = {}  # Cache historical patterns
        self.current_patterns = {}  # Current pattern state for each coin
        self.skill_indicators = {}  # Skill-based indicators for each coin
        self.market_phase = "normal"  # bull, bear, volatile, normal
        self.time_compression = 52  # 1 year = 1 week
        self.update_interval = 600  # 10 minutes (compressed from ~3 hours real time)
        self.balancing_update_counter = 0  # Track updates for periodic balancing adjustments
        
    async def initialize(self):
        """Initialize the advanced simulator with real data"""
        print("🔄 Initializing advanced crypto simulator...")
        
        # Fetch real historical data for all coins
        for bot_ticker in CRYPTO_COINS.keys():
            print(f"📊 Fetching pattern data for {bot_ticker}...")
            try:
                pattern_data = await self.data_fetcher.get_pattern_for_coin(bot_ticker)
                
                if pattern_data and len(pattern_data) > 10:  # Ensure we have enough data
                    # Compress timeframe: 1 year -> 1 week
                    compressed_data = await self.data_fetcher.compress_timeframe(pattern_data, self.time_compression)
                    self.pattern_cache[bot_ticker] = compressed_data
                    
                    print(f"✅ Loaded {len(compressed_data)} data points for {bot_ticker}")
                else:
                    print(f"⚠️ Insufficient data for {bot_ticker}, using fallback")
                    # Generate fallback pattern data
                    fallback_data = self.data_fetcher._generate_fallback_data(365)
                    compressed_data = await self.data_fetcher.compress_timeframe(fallback_data, self.time_compression)
                    self.pattern_cache[bot_ticker] = compressed_data
                    print(f"📊 Generated {len(compressed_data)} fallback data points for {bot_ticker}")
                
                # Get current price from database for base price
                coin_data = await CryptoModels.get_coin(bot_ticker)
                base_price = coin_data["current_price"] if coin_data else 1.0
                
                # Initialize current position in pattern
                self.current_patterns[bot_ticker] = {
                    "data_index": 0,
                    "base_price": base_price,
                    "pattern_scale": 1.0,
                    "trend_momentum": 0.0
                }
                
            except Exception as e:
                print(f"❌ Error initializing {bot_ticker}: {e}")
                # Still initialize with empty data to prevent crashes
                self.pattern_cache[bot_ticker] = []
                coin_data = await CryptoModels.get_coin(bot_ticker)
                base_price = coin_data["current_price"] if coin_data else 1.0
                
                self.current_patterns[bot_ticker] = {
                    "data_index": 0,
                    "base_price": base_price,
                    "pattern_scale": 1.0,
                    "trend_momentum": 0.0
                }
        
        # Initialize skill indicators
        await self._initialize_skill_indicators()
        print("🎯 Advanced simulator initialized successfully!")
    
    async def _initialize_skill_indicators(self):
        """Initialize skill-based indicators for each coin"""
        for ticker in CRYPTO_COINS.keys():
            self.skill_indicators[ticker] = {
                "moving_averages": {
                    "5_period": 0,
                    "15_period": 0,
                    "crossover_signal": "none"
                },
                "trend_strength": 0,
                "volatility_signal": "normal",
                "support_resistance": {
                    "support": 0,
                    "resistance": 0,
                    "near_level": False
                },
                "pattern_signal": {
                    "signal": "hold",
                    "confidence": 0,
                    "strength": "weak"
                }
            }
    
    async def update_market_prices(self):
        """Update all coin prices using advanced pattern-based system"""
        try:
            # Determine market phase
            await self._update_market_phase()
            
            # Periodic win rate balancing adjustment (every 10 updates)
            self.balancing_update_counter += 1
            if self.balancing_update_counter >= 10:
                await self._adjust_win_rate_balancing()
                self.balancing_update_counter = 0
            
            price_updates = []
            
            for ticker in CRYPTO_COINS.keys():
                new_price = await self._calculate_advanced_price(ticker)
                if new_price:
                    # Get old price for change calculation
                    coin = await CryptoModels.get_coin(ticker)
                    old_price = coin["current_price"] if coin else new_price
                    change_percent = ((new_price - old_price) / old_price) * 100 if old_price > 0 else 0
                    
                    # Update skill indicators
                    await self._update_skill_indicators(ticker, new_price)
                    
                    # Store price update with change info
                    price_updates.append({
                        "ticker": ticker,
                        "price": new_price,
                        "old_price": old_price,
                        "change_percent": change_percent,
                        "timestamp": datetime.utcnow()
                    })
            
            # Batch update prices
            for update in price_updates:
                await CryptoModels.update_coin_price(
                    update["ticker"], 
                    update["price"], 
                    update["timestamp"]
                )
                
                # Check and execute trigger orders for this price update
                executed_triggers = await check_and_execute_triggers(
                    update["ticker"], 
                    update["price"]
                )
                
                # Log executed triggers for monitoring
                if executed_triggers:
                    print(f"🎯 Executed {len(executed_triggers)} trigger orders for {update['ticker']} at ${update['price']:.4f}")
            
            return price_updates
            
        except Exception as e:
            print(f"Error in advanced price update: {e}")
            return []
    
    async def _calculate_advanced_price(self, ticker: str) -> Optional[float]:
        """Calculate new price using real patterns + controlled randomness"""
        try:
            current_coin = await CryptoModels.get_coin(ticker)
            if not current_coin:
                return None
                
            current_price = current_coin["current_price"]
            pattern_state = self.current_patterns.get(ticker, {})
            pattern_data = self.pattern_cache.get(ticker, [])
            
            # Base price change from real pattern
            pattern_change = 0
            if pattern_data and pattern_state.get("data_index", 0) < len(pattern_data) - 1:
                pattern_change = self._get_pattern_price_change(ticker, pattern_data, pattern_state)
            
            # Market phase influence
            phase_multiplier = self._get_market_phase_multiplier()
            
            # Skill-based predictable component (30% of movement)
            skill_component = self._calculate_skill_component(ticker)
            
            # Random component (70% of movement) - this is what makes it challenging
            random_component = self._calculate_random_component(ticker)
            
            # Combine all components (before balancing)
            total_change = (
                pattern_change * phase_multiplier * 0.3 + 
                skill_component * 0.3 + 
                random_component * 0.7
            )
            
            # Apply win rate balancing mechanisms
            balancing_result = await self.win_rate_balancer.apply_balancing_mechanisms(ticker, total_change)
            final_change = balancing_result["final_change"]
            
            # Log significant balancing effects
            if balancing_result["effects_applied"]:
                effects = ", ".join(balancing_result["effects_applied"])
                print(f"⚖️ {ticker} balancing: {effects} (severity: {balancing_result['severity']})")
            
            # Apply the final change
            new_price = current_price * (1 + final_change)
            
            # Ensure price bounds (prevent too extreme moves)
            min_price = current_price * 0.01  # Max 99% drop
            max_price = current_price * 100    # Max 10,000% gain
            new_price = max(min_price, min(new_price, max_price))
            
            # Ensure minimum price floor ($0.10)
            new_price = max(new_price, MINIMUM_PRICE_FLOOR)
            
            # Update pattern state
            if pattern_data:
                pattern_state["data_index"] = (pattern_state.get("data_index", 0) + 1) % len(pattern_data)
                self.current_patterns[ticker] = pattern_state
            
            return round(new_price, 6)
            
        except Exception as e:
            print(f"Error calculating price for {ticker}: {e}")
            return None
    
    def _get_pattern_price_change(self, ticker: str, pattern_data: List[Dict], pattern_state: Dict) -> float:
        """Extract price change from real pattern data"""
        try:
            current_index = pattern_state.get("data_index", 0)
            next_index = (current_index + 1) % len(pattern_data)
            
            current_pattern_price = pattern_data[current_index]["price"]
            next_pattern_price = pattern_data[next_index]["price"]
            
            # Calculate percentage change
            pattern_change = (next_pattern_price - current_pattern_price) / current_pattern_price
            
            # Scale the change (real crypto moves are already wild, but we can adjust)
            scale_factor = pattern_state.get("pattern_scale", 1.0)
            return pattern_change * scale_factor
            
        except Exception as e:
            print(f"Error getting pattern change for {ticker}: {e}")
            return 0
    
    def _get_market_phase_multiplier(self) -> float:
        """Get multiplier based on current market phase"""
        multipliers = {
            "bull": 1.3,      # Amplify upward moves
            "bear": 1.2,      # Amplify downward moves  
            "volatile": 1.5,  # Amplify all moves
            "normal": 1.0     # No amplification
        }
        return multipliers.get(self.market_phase, 1.0)
    
    def _calculate_skill_component(self, ticker: str) -> float:
        """Calculate predictable component that skilled traders can exploit"""
        try:
            indicators = self.skill_indicators.get(ticker, {})
            
            # Moving average crossover signal
            ma_signal = indicators.get("moving_averages", {}).get("crossover_signal", "none")
            ma_component = 0
            if ma_signal == "bullish":
                ma_component = 0.02  # 2% bullish bias
            elif ma_signal == "bearish":
                ma_component = -0.02  # 2% bearish bias
            
            # Trend strength
            trend_strength = indicators.get("trend_strength", 0)
            trend_component = trend_strength * 0.03  # Up to 3% from trend
            
            # Support/resistance levels
            sr_info = indicators.get("support_resistance", {})
            sr_component = 0
            if sr_info.get("near_level", False):
                # Slight bounce from support/resistance
                sr_component = random.uniform(-0.01, 0.01)
            
            return ma_component + trend_component + sr_component
            
        except Exception as e:
            print(f"Error calculating skill component for {ticker}: {e}")
            return 0
    
    def _calculate_random_component(self, ticker: str) -> float:
        """Calculate random component - this is what makes most people lose"""
        try:
            # Base random volatility (1% to 100% possible)
            base_volatility = random.uniform(0.01, 0.15)  # 1% to 15% base
            
            # Occasional extreme moves (the 100% swings you wanted)
            if random.random() < 0.05:  # 5% chance of extreme move
                extreme_move = random.uniform(0.3, 1.0)  # 30% to 100% move
                direction = random.choice([-1, 1])
                return extreme_move * direction
            
            # Occasional large moves
            if random.random() < 0.15:  # 15% chance of large move
                large_move = random.uniform(0.1, 0.3)  # 10% to 30% move
                direction = random.choice([-1, 1])
                return large_move * direction
            
            # Normal random movement
            direction = random.choice([-1, 1])
            return base_volatility * direction
            
        except Exception as e:
            print(f"Error calculating random component for {ticker}: {e}")
            return 0
    
    async def _update_market_phase(self):
        """Update overall market phase based on recent performance"""
        try:
            # Get recent price data for all coins
            total_change = 0
            coin_count = 0
            
            for ticker in CRYPTO_COINS.keys():
                coin = await CryptoModels.get_coin(ticker)
                if coin:
                    # Compare to price from 1 hour ago (simplified)
                    current_price = coin["current_price"]
                    starting_price = coin.get("starting_price", current_price)
                    
                    change = (current_price - starting_price) / starting_price
                    total_change += change
                    coin_count += 1
            
            if coin_count == 0:
                return
            
            avg_change = total_change / coin_count
            
            # Determine market phase
            if avg_change > 0.1:  # 10% average gain
                self.market_phase = "bull"
            elif avg_change < -0.1:  # 10% average loss
                self.market_phase = "bear"
            elif abs(avg_change) > 0.05:  # High volatility
                self.market_phase = "volatile"
            else:
                self.market_phase = "normal"
                
        except Exception as e:
            print(f"Error updating market phase: {e}")
    
    async def _update_skill_indicators(self, ticker: str, new_price: float):
        """Update skill-based indicators for a coin"""
        try:
            # Get recent price history
            price_history = await CryptoModels.get_price_history(ticker, hours=2)
            if not price_history:
                return
            
            # Add current price to history
            price_history.append({"price": new_price, "timestamp": datetime.utcnow()})
            
            # Calculate indicators
            indicators = self.skill_indicators.get(ticker, {})
            
            # Moving averages
            if len(price_history) >= 15:
                prices = [p["price"] for p in price_history[-15:]]
                ma_5 = sum(prices[-5:]) / 5
                ma_15 = sum(prices) / 15
                
                # Detect crossover
                prev_ma_5 = sum(prices[-6:-1]) / 5 if len(prices) >= 6 else ma_5
                prev_ma_15 = sum(prices[:-1]) / 14 if len(prices) >= 15 else ma_15
                
                crossover_signal = "none"
                if prev_ma_5 <= prev_ma_15 and ma_5 > ma_15:
                    crossover_signal = "bullish"
                elif prev_ma_5 >= prev_ma_15 and ma_5 < ma_15:
                    crossover_signal = "bearish"
                
                indicators["moving_averages"] = {
                    "5_period": ma_5,
                    "15_period": ma_15,
                    "crossover_signal": crossover_signal
                }
            
            # Trend strength
            if len(price_history) >= 10:
                prices = [p["price"] for p in price_history[-10:]]
                trend_strength = self.pattern_analyzer._calculate_trend_strength(prices)
                indicators["trend_strength"] = trend_strength
            
            # Pattern analysis
            if len(price_history) >= 20:
                patterns = self.pattern_analyzer.detect_patterns(price_history)
                trading_signal = self.pattern_analyzer.generate_trading_signal(patterns)
                indicators["pattern_signal"] = trading_signal
                
                # Support/resistance
                sr_info = patterns.get("support_resistance", {})
                indicators["support_resistance"] = sr_info
            
            # Volatility signal
            if len(price_history) >= 5:
                recent_prices = [p["price"] for p in price_history[-5:]]
                volatility = self._calculate_recent_volatility(recent_prices)
                if volatility > 0.1:
                    indicators["volatility_signal"] = "high"
                elif volatility > 0.05:
                    indicators["volatility_signal"] = "elevated"
                else:
                    indicators["volatility_signal"] = "normal"
            
            self.skill_indicators[ticker] = indicators
            
        except Exception as e:
            print(f"Error updating skill indicators for {ticker}: {e}")
    
    def _calculate_recent_volatility(self, prices: List[float]) -> float:
        """Calculate recent volatility from price list"""
        if len(prices) < 2:
            return 0
        
        changes = []
        for i in range(1, len(prices)):
            change = abs((prices[i] - prices[i-1]) / prices[i-1])
            changes.append(change)
        
        return sum(changes) / len(changes) if changes else 0
    
    async def get_market_analysis(self, ticker: str) -> Dict:
        """Get detailed market analysis for skilled traders"""
        try:
            indicators = self.skill_indicators.get(ticker, {})
            coin = await CryptoModels.get_coin(ticker)
            
            if not coin:
                return {}
            
            analysis = {
                "ticker": ticker,
                "current_price": coin["current_price"],
                "market_phase": self.market_phase,
                "technical_indicators": {
                    "moving_averages": indicators.get("moving_averages", {}),
                    "trend_strength": indicators.get("trend_strength", 0),
                    "volatility_signal": indicators.get("volatility_signal", "normal"),
                    "pattern_signal": indicators.get("pattern_signal", {})
                },
                "support_resistance": indicators.get("support_resistance", {}),
                "trading_recommendation": self._generate_trading_recommendation(ticker, indicators)
            }
            
            return analysis
            
        except Exception as e:
            print(f"Error getting market analysis for {ticker}: {e}")
            return {}
    
    def _generate_trading_recommendation(self, ticker: str, indicators: Dict) -> Dict:
        """Generate trading recommendation based on indicators"""
        try:
            signals = []
            confidence = 0
            
            # Moving average signal
            ma_signal = indicators.get("moving_averages", {}).get("crossover_signal", "none")
            if ma_signal != "none":
                signals.append(f"MA Crossover: {ma_signal}")
                confidence += 0.3
            
            # Pattern signal
            pattern_signal = indicators.get("pattern_signal", {})
            if pattern_signal.get("confidence", 0) > 0.5:
                signals.append(f"Pattern: {pattern_signal.get('signal', 'hold')}")
                confidence += pattern_signal.get("confidence", 0) * 0.4
            
            # Trend signal
            trend_strength = indicators.get("trend_strength", 0)
            if abs(trend_strength) > 0.02:
                direction = "bullish" if trend_strength > 0 else "bearish"
                signals.append(f"Trend: {direction}")
                confidence += min(abs(trend_strength) * 10, 0.3)
            
            # Overall recommendation
            if confidence > 0.6:
                recommendation = "STRONG BUY" if any("bullish" in s for s in signals) else "STRONG SELL"
            elif confidence > 0.4:
                recommendation = "BUY" if any("bullish" in s for s in signals) else "SELL"
            else:
                recommendation = "HOLD"
            
            return {
                "recommendation": recommendation,
                "confidence": min(confidence, 1.0),
                "signals": signals,
                "risk_level": "HIGH" if confidence > 0.7 else "MEDIUM" if confidence > 0.4 else "LOW"
            }
            
        except Exception as e:
            print(f"Error generating recommendation for {ticker}: {e}")
            return {"recommendation": "HOLD", "confidence": 0, "signals": [], "risk_level": "UNKNOWN"}
    
    async def _adjust_win_rate_balancing(self):
        """Periodically adjust win rate balancing based on current performance"""
        try:
            stats = await self.win_rate_balancer.get_current_win_rate_stats()
            current_win_rate = stats["current_win_rate"]
            
            if stats["total_traders"] >= 5:  # Only adjust if we have enough data
                self.win_rate_balancer.adjust_balancing_intensity(current_win_rate)
                
                if stats["needs_more_balancing"]:
                    print(f"📊 Win rate monitoring: {current_win_rate:.1%} (target: {stats['target_win_rate']:.1%}) - Increasing balancing")
                else:
                    print(f"✅ Win rate balanced: {current_win_rate:.1%}")
            
        except Exception as e:
            print(f"Error adjusting win rate balancing: {e}")
    
    async def get_balancing_status(self) -> Dict:
        """Get current balancing status for admin monitoring"""
        try:
            win_rate_stats = await self.win_rate_balancer.get_current_win_rate_stats()
            balancing_info = self.win_rate_balancer.get_balancing_info()
            
            return {
                "win_rate_stats": win_rate_stats,
                "balancing_config": balancing_info,
                "market_phase": self.market_phase,
                "advanced_mode": True,
                "time_compression": f"1 year = 1 week ({self.time_compression}x)"
            }
            
        except Exception as e:
            print(f"Error getting balancing status: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.data_fetcher.close()