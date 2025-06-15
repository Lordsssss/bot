"""
Advanced crypto data fetcher for hybrid real/fictional price system
"""
import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import json

class CryptoDataFetcher:
    """Fetches real crypto data for pattern analysis"""
    
    # Map your meme coins to real crypto patterns
    PATTERN_MAPPING = {
        "DOGE2": "dogecoin",      # DOGE patterns
        "MEME": "pepe",           # PEPE's wild swings  
        "BOOM": "bitcoin",        # BTC for "stability"
        "YOLO": "pepe",           # PEPE chaos
        "HODL": "bitcoin",        # BTC diamond hands
        "REKT": "shiba-inu",      # SHIB volatility
        "PUMP": "pepe",           # PEPE pump style
        "DUMP": "shiba-inu",      # SHIB dump style
        "MOON": "dogecoin",       # DOGE moon missions
        "Chad": "ethereum"        # ETH for alpha energy
    }
    
    def __init__(self):
        self.api_base = "https://api.coingecko.com/api/v3"
        self.session = None
        self.rate_limit_delay = 2  # 30 calls/min = 2 sec delay
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            
    async def fetch_historical_data(self, coin_id: str, days: int = 365) -> Optional[List[Dict]]:
        """Fetch real historical price data"""
        try:
            session = await self.get_session()
            url = f"{self.api_base}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily" if days > 90 else "hourly"
            }
            
            await asyncio.sleep(self.rate_limit_delay)  # Rate limiting
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    prices = data.get("prices", [])
                    
                    if not prices:
                        print(f"No price data returned for {coin_id}")
                        return self._generate_fallback_data(days)
                    
                    # Format data
                    formatted_data = []
                    for price_point in prices:
                        timestamp, price = price_point
                        formatted_data.append({
                            "timestamp": datetime.fromtimestamp(timestamp / 1000),
                            "price": price
                        })
                    
                    print(f"✅ Fetched {len(formatted_data)} data points for {coin_id}")
                    return formatted_data
                elif response.status == 429:  # Rate limited
                    print(f"Rate limited for {coin_id}, using fallback data")
                    return self._generate_fallback_data(days)
                else:
                    print(f"API Error {response.status} for {coin_id}, using fallback")
                    return self._generate_fallback_data(days)
                    
        except Exception as e:
            print(f"Error fetching data for {coin_id}: {e}, using fallback")
            return self._generate_fallback_data(days)
    
    def _generate_fallback_data(self, days: int) -> List[Dict]:
        """Generate realistic fallback crypto price data"""
        data = []
        base_price = random.uniform(0.001, 100.0)
        current_price = base_price
        
        # Generate realistic crypto-like price movements
        for i in range(min(days, 365)):  # Cap at 365 points
            # Crypto-style volatility (high volatility with occasional massive moves)
            if random.random() < 0.05:  # 5% chance of extreme move
                change = random.uniform(-0.5, 1.0)  # -50% to +100%
            else:
                change = random.uniform(-0.1, 0.1)  # Normal -10% to +10%
            
            current_price = max(current_price * (1 + change), 0.0001)
            
            timestamp = datetime.utcnow() - timedelta(days=days-i)
            data.append({
                "timestamp": timestamp,
                "price": current_price
            })
        
        print(f"📊 Generated {len(data)} fallback data points")
        return data
    
    async def get_pattern_for_coin(self, bot_ticker: str) -> Optional[List[Dict]]:
        """Get real crypto pattern data for a bot coin"""
        real_coin_id = self.PATTERN_MAPPING.get(bot_ticker)
        if not real_coin_id:
            return None
            
        return await self.fetch_historical_data(real_coin_id, days=365)
    
    async def calculate_volatility_metrics(self, price_data: List[Dict]) -> Dict:
        """Calculate volatility metrics from price data"""
        if len(price_data) < 2:
            return {"daily_volatility": 0.05, "max_swing": 0.10}
        
        daily_changes = []
        for i in range(1, len(price_data)):
            prev_price = price_data[i-1]["price"]
            curr_price = price_data[i]["price"]
            daily_change = abs((curr_price - prev_price) / prev_price)
            daily_changes.append(daily_change)
        
        avg_volatility = sum(daily_changes) / len(daily_changes)
        max_swing = max(daily_changes) if daily_changes else 0.05
        
        return {
            "daily_volatility": min(max(avg_volatility, 0.01), 1.0),  # 1%-100%
            "max_swing": min(max(max_swing, 0.05), 1.0),
            "volatility_trend": "increasing" if daily_changes[-5:] > daily_changes[:5] else "stable"
        }
    
    async def compress_timeframe(self, price_data: List[Dict], compression_ratio: int = 52) -> List[Dict]:
        """Compress 1 year of data into 1 week (52x compression)"""
        if not price_data:
            return []
        
        # Calculate target data points for 1 week (1 point per 10 minutes = 1008 points/week)
        target_points = 1008
        source_points = len(price_data)
        
        if source_points <= target_points:
            return price_data
        
        # Sample data points evenly
        step = source_points / target_points
        compressed_data = []
        
        for i in range(target_points):
            index = int(i * step)
            if index < source_points:
                compressed_data.append(price_data[index])
        
        return compressed_data


class PatternAnalyzer:
    """Analyzes patterns for skill-based trading opportunities"""
    
    def __init__(self):
        self.trend_window = 20  # Look at last 20 price points for trends
        
    def detect_patterns(self, price_history: List[Dict]) -> Dict:
        """Detect subtle patterns that skilled traders can exploit"""
        if len(price_history) < self.trend_window:
            return {"pattern": "none", "confidence": 0}
        
        recent_prices = [p["price"] for p in price_history[-self.trend_window:]]
        
        # Moving average crossover (subtle signal)
        short_ma = sum(recent_prices[-5:]) / 5
        long_ma = sum(recent_prices[-15:]) / 15
        
        # Trend detection
        trend_strength = self._calculate_trend_strength(recent_prices)
        
        # Support/Resistance levels
        support_resistance = self._find_support_resistance(recent_prices)
        
        # Volatility clustering (periods of high volatility)
        volatility_cluster = self._detect_volatility_clustering(price_history)
        
        patterns = {
            "ma_crossover": {
                "signal": "bullish" if short_ma > long_ma else "bearish",
                "strength": abs(short_ma - long_ma) / long_ma,
                "confidence": min(abs(short_ma - long_ma) / long_ma * 10, 1.0)
            },
            "trend": {
                "direction": "up" if trend_strength > 0.02 else "down" if trend_strength < -0.02 else "sideways",
                "strength": abs(trend_strength),
                "confidence": min(abs(trend_strength) * 5, 1.0)
            },
            "support_resistance": support_resistance,
            "volatility_cluster": volatility_cluster
        }
        
        return patterns
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """Calculate trend strength using linear regression slope"""
        n = len(prices)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(prices) / n
        
        numerator = sum((x_values[i] - x_mean) * (prices[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope / y_mean  # Normalize by price
    
    def _find_support_resistance(self, prices: List[float]) -> Dict:
        """Find potential support and resistance levels"""
        max_price = max(prices)
        min_price = min(prices)
        current_price = prices[-1]
        
        # Simple support/resistance based on recent highs/lows
        resistance = max_price
        support = min_price
        
        # Check if price is near support/resistance
        near_resistance = abs(current_price - resistance) / resistance < 0.02
        near_support = abs(current_price - support) / support < 0.02
        
        return {
            "resistance": resistance,
            "support": support,
            "near_resistance": near_resistance,
            "near_support": near_support,
            "confidence": 0.7 if near_resistance or near_support else 0.3
        }
    
    def _detect_volatility_clustering(self, price_history: List[Dict]) -> Dict:
        """Detect periods of high volatility (opportunity for big moves)"""
        if len(price_history) < 10:
            return {"clustering": False, "confidence": 0}
        
        # Calculate recent volatility
        recent_volatility = []
        for i in range(1, min(10, len(price_history))):
            prev_price = price_history[-i-1]["price"]
            curr_price = price_history[-i]["price"]
            volatility = abs((curr_price - prev_price) / prev_price)
            recent_volatility.append(volatility)
        
        avg_volatility = sum(recent_volatility) / len(recent_volatility)
        high_volatility_threshold = 0.05  # 5% moves
        
        is_clustering = avg_volatility > high_volatility_threshold
        
        return {
            "clustering": is_clustering,
            "average_volatility": avg_volatility,
            "confidence": min(avg_volatility / high_volatility_threshold, 1.0) if is_clustering else 0
        }
    
    def generate_trading_signal(self, patterns: Dict) -> Dict:
        """Generate a trading signal based on pattern analysis"""
        signals = []
        total_confidence = 0
        
        # Moving average signal
        ma_pattern = patterns.get("ma_crossover", {})
        if ma_pattern.get("confidence", 0) > 0.3:
            signals.append({
                "type": "ma_crossover",
                "direction": ma_pattern["signal"],
                "confidence": ma_pattern["confidence"]
            })
            total_confidence += ma_pattern["confidence"]
        
        # Trend signal
        trend_pattern = patterns.get("trend", {})
        if trend_pattern.get("confidence", 0) > 0.4:
            signals.append({
                "type": "trend",
                "direction": "bullish" if trend_pattern["direction"] == "up" else "bearish",
                "confidence": trend_pattern["confidence"]
            })
            total_confidence += trend_pattern["confidence"]
        
        # Support/Resistance signal
        sr_pattern = patterns.get("support_resistance", {})
        if sr_pattern.get("confidence", 0) > 0.6:
            direction = "bullish" if sr_pattern.get("near_support") else "bearish" if sr_pattern.get("near_resistance") else "neutral"
            signals.append({
                "type": "support_resistance",
                "direction": direction,
                "confidence": sr_pattern["confidence"]
            })
            total_confidence += sr_pattern["confidence"]
        
        # Overall signal
        if not signals:
            return {"signal": "hold", "confidence": 0, "reasons": []}
        
        # Weighted average of signals
        bullish_weight = sum(s["confidence"] for s in signals if s["direction"] == "bullish")
        bearish_weight = sum(s["confidence"] for s in signals if s["direction"] == "bearish")
        
        if bullish_weight > bearish_weight:
            overall_signal = "buy"
            confidence = bullish_weight / total_confidence
        elif bearish_weight > bullish_weight:
            overall_signal = "sell"
            confidence = bearish_weight / total_confidence
        else:
            overall_signal = "hold"
            confidence = 0.5
        
        return {
            "signal": overall_signal,
            "confidence": confidence,
            "reasons": [s["type"] for s in signals],
            "strength": "strong" if confidence > 0.7 else "medium" if confidence > 0.4 else "weak"
        }