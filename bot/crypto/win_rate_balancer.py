"""
Win rate balancing system to reduce profitability and add challenge
"""
import random
from typing import Dict, List
from datetime import datetime, timedelta
from .models import CryptoModels

class WinRateBalancer:
    """Balances win rates to make trading more challenging"""
    
    def __init__(self):
        self.target_win_rate = 0.35  # Target 35% win rate (down from current ~70%+)
        self.whale_manipulation_chance = 0.08  # 8% chance per update
        self.market_maker_advantage = 0.02  # Market makers get 2% edge
        self.slippage_factor = 0.005  # 0.5% slippage on large trades
        self.pump_and_dump_frequency = 0.03  # 3% chance of pump and dump
        
    async def apply_balancing_mechanisms(self, ticker: str, base_price_change: float) -> Dict:
        """Apply various balancing mechanisms to reduce win rates"""
        try:
            balancing_effects = {
                "original_change": base_price_change,
                "final_change": base_price_change,
                "effects_applied": [],
                "severity": "none"
            }
            
            # 1. Whale manipulation (sudden unexpected moves)
            whale_effect = await self._apply_whale_manipulation(ticker)
            if whale_effect["applied"]:
                balancing_effects["final_change"] += whale_effect["impact"]
                balancing_effects["effects_applied"].append("whale_manipulation")
                balancing_effects["severity"] = "high"
            
            # 2. Market maker advantage (reduces retail trader success)
            mm_effect = self._apply_market_maker_advantage(base_price_change)
            if mm_effect["applied"]:
                balancing_effects["final_change"] += mm_effect["impact"]
                balancing_effects["effects_applied"].append("market_maker_advantage")
                if balancing_effects["severity"] == "none":
                    balancing_effects["severity"] = "low"
            
            # 3. Pump and dump schemes
            pnd_effect = await self._apply_pump_and_dump(ticker)
            if pnd_effect["applied"]:
                balancing_effects["final_change"] += pnd_effect["impact"]
                balancing_effects["effects_applied"].append("pump_and_dump")
                balancing_effects["severity"] = "extreme"
            
            # 4. Hidden liquidity issues (price gaps)
            liquidity_effect = self._apply_liquidity_gaps(base_price_change)
            if liquidity_effect["applied"]:
                balancing_effects["final_change"] += liquidity_effect["impact"]
                balancing_effects["effects_applied"].append("liquidity_gap")
                if balancing_effects["severity"] in ["none", "low"]:
                    balancing_effects["severity"] = "medium"
            
            # 5. Transaction timing delays (cause missed opportunities)
            timing_effect = self._apply_timing_delays(base_price_change)
            if timing_effect["applied"]:
                balancing_effects["final_change"] += timing_effect["impact"]
                balancing_effects["effects_applied"].append("timing_delay")
                if balancing_effects["severity"] == "none":
                    balancing_effects["severity"] = "low"
            
            # Ensure price change isn't completely broken
            balancing_effects["final_change"] = max(-0.99, min(balancing_effects["final_change"], 5.0))
            
            return balancing_effects
            
        except Exception as e:
            print(f"Error in win rate balancing for {ticker}: {e}")
            return {
                "original_change": base_price_change,
                "final_change": base_price_change,
                "effects_applied": [],
                "severity": "error"
            }
    
    async def _apply_whale_manipulation(self, ticker: str) -> Dict:
        """Apply whale manipulation effects"""
        try:
            if random.random() > self.whale_manipulation_chance:
                return {"applied": False, "impact": 0}
            
            # Get recent trading volume (simplified)
            recent_prices = await CryptoModels.get_price_history(ticker, hours=1)
            
            # Whales are more likely to manipulate during high activity
            manipulation_strength = random.uniform(0.1, 0.4)  # 10% to 40% sudden move
            
            # Whales prefer to dump on retail traders (more bearish moves)
            direction = random.choice([-1, -1, -1, 1])  # 75% chance bearish
            
            impact = manipulation_strength * direction
            
            print(f"🐋 Whale manipulation on {ticker}: {impact*100:+.1f}%")
            
            return {
                "applied": True,
                "impact": impact,
                "message": f"Large whale movement detected on {ticker}"
            }
            
        except Exception as e:
            print(f"Error in whale manipulation for {ticker}: {e}")
            return {"applied": False, "impact": 0}
    
    def _apply_market_maker_advantage(self, base_change: float) -> Dict:
        """Apply market maker advantage (reduces retail success)"""
        try:
            # Market makers profit from retail trader losses
            if random.random() > 0.3:  # 30% chance to apply
                return {"applied": False, "impact": 0}
            
            # Market makers dampen moves that would be profitable for retail
            if abs(base_change) > 0.05:  # If move is > 5%
                # Reduce the move by the market maker advantage
                dampening = self.market_maker_advantage
                if base_change > 0:
                    impact = -dampening  # Reduce pumps
                else:
                    impact = dampening   # Reduce dumps
                
                return {
                    "applied": True,
                    "impact": impact,
                    "message": "Market maker intervention"
                }
            
            return {"applied": False, "impact": 0}
            
        except Exception as e:
            print(f"Error in market maker advantage: {e}")
            return {"applied": False, "impact": 0}
    
    async def _apply_pump_and_dump(self, ticker: str) -> Dict:
        """Apply pump and dump schemes"""
        try:
            if random.random() > self.pump_and_dump_frequency:
                return {"applied": False, "impact": 0}
            
            # Pump and dump phases
            pnd_phase = random.choice(["pump", "dump", "coordinated"])
            
            if pnd_phase == "pump":
                # Artificial pump (will be followed by dump later)
                impact = random.uniform(0.2, 0.8)  # 20% to 80% pump
                message = f"⚡ Coordinated pump detected on {ticker}! Dump incoming..."
                
            elif pnd_phase == "dump":
                # The inevitable dump
                impact = random.uniform(-0.6, -0.3)  # 30% to 60% dump
                message = f"💥 Pump and dump scheme collapse on {ticker}!"
                
            else:  # coordinated
                # Coordinated buy/sell to confuse retail
                impact = random.uniform(-0.3, 0.3)
                message = f"🎭 Market manipulation detected on {ticker}"
            
            print(f"🎯 Pump & Dump on {ticker}: {impact*100:+.1f}%")
            
            return {
                "applied": True,
                "impact": impact,
                "message": message
            }
            
        except Exception as e:
            print(f"Error in pump and dump for {ticker}: {e}")
            return {"applied": False, "impact": 0}
    
    def _apply_liquidity_gaps(self, base_change: float) -> Dict:
        """Apply liquidity gaps that cause price slippage"""
        try:
            # More likely during large moves
            gap_chance = min(0.15, abs(base_change) * 2)  # Up to 15% chance
            
            if random.random() > gap_chance:
                return {"applied": False, "impact": 0}
            
            # Liquidity gaps cause slippage against the trader
            slippage = random.uniform(0.01, 0.05)  # 1% to 5% slippage
            
            # Slippage always works against the current move
            if base_change > 0:
                impact = -slippage  # Reduce gains
            else:
                impact = -slippage  # Increase losses (double whammy)
            
            return {
                "applied": True,
                "impact": impact,
                "message": "Low liquidity causing slippage"
            }
            
        except Exception as e:
            print(f"Error in liquidity gaps: {e}")
            return {"applied": False, "impact": 0}
    
    def _apply_timing_delays(self, base_change: float) -> Dict:
        """Apply timing delays that cause missed opportunities"""
        try:
            if random.random() > 0.2:  # 20% chance
                return {"applied": False, "impact": 0}
            
            # Timing delays cause you to buy high and sell low
            delay_penalty = random.uniform(0.005, 0.02)  # 0.5% to 2% penalty
            
            # Penalty always works against favorable moves
            if abs(base_change) > 0.03:  # Only on significant moves
                if base_change > 0:
                    impact = -delay_penalty  # Miss some of the pump
                else:
                    impact = -delay_penalty  # Get worse price on dump
                
                return {
                    "applied": True,
                    "impact": impact,
                    "message": "Network congestion causing delays"
                }
            
            return {"applied": False, "impact": 0}
            
        except Exception as e:
            print(f"Error in timing delays: {e}")
            return {"applied": False, "impact": 0}
    
    async def get_current_win_rate_stats(self) -> Dict:
        """Get current win rate statistics across all users"""
        try:
            # Get all portfolio data
            portfolios = await CryptoModels.get_portfolio_leaderboard(limit=100)
            
            total_traders = len(portfolios)
            profitable_traders = len([p for p in portfolios if p.get("all_time_profit_loss", 0) > 0])
            
            current_win_rate = profitable_traders / total_traders if total_traders > 0 else 0
            
            return {
                "total_traders": total_traders,
                "profitable_traders": profitable_traders,
                "current_win_rate": current_win_rate,
                "target_win_rate": self.target_win_rate,
                "needs_more_balancing": current_win_rate > self.target_win_rate,
                "balancing_strength": min(1.0, (current_win_rate - self.target_win_rate) / 0.2) if current_win_rate > self.target_win_rate else 0
            }
            
        except Exception as e:
            print(f"Error getting win rate stats: {e}")
            return {
                "total_traders": 0,
                "profitable_traders": 0,
                "current_win_rate": 0,
                "target_win_rate": self.target_win_rate,
                "needs_more_balancing": False,
                "balancing_strength": 0
            }
    
    def adjust_balancing_intensity(self, current_win_rate: float):
        """Dynamically adjust balancing intensity based on current win rate"""
        try:
            if current_win_rate > self.target_win_rate + 0.15:  # Way too high (>50%)
                # Increase all balancing mechanisms
                self.whale_manipulation_chance = min(0.15, self.whale_manipulation_chance * 1.5)
                self.pump_and_dump_frequency = min(0.08, self.pump_and_dump_frequency * 1.5)
                print(f"🔥 Increasing balancing intensity - win rate too high: {current_win_rate:.1%}")
                
            elif current_win_rate < self.target_win_rate - 0.1:  # Too low (<25%)
                # Decrease balancing mechanisms
                self.whale_manipulation_chance = max(0.05, self.whale_manipulation_chance * 0.8)
                self.pump_and_dump_frequency = max(0.02, self.pump_and_dump_frequency * 0.8)
                print(f"📉 Decreasing balancing intensity - win rate too low: {current_win_rate:.1%}")
                
            else:
                print(f"⚖️ Win rate balanced: {current_win_rate:.1%} (target: {self.target_win_rate:.1%})")
                
        except Exception as e:
            print(f"Error adjusting balancing intensity: {e}")
    
    def get_balancing_info(self) -> Dict:
        """Get current balancing configuration info"""
        return {
            "target_win_rate": f"{self.target_win_rate:.1%}",
            "whale_manipulation_chance": f"{self.whale_manipulation_chance:.1%}",
            "pump_and_dump_frequency": f"{self.pump_and_dump_frequency:.1%}",
            "market_maker_advantage": f"{self.market_maker_advantage:.1%}",
            "slippage_factor": f"{self.slippage_factor:.1%}",
            "description": "Advanced balancing to create realistic trading challenges"
        }