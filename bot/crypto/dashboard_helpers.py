"""
Helper functions for crypto dashboard integration
"""
import discord
from typing import Dict, Any

from .portfolio import PortfolioManager
from .constants import CRYPTO_COINS
from .models import get_crypto_portfolio, get_crypto_prices, get_crypto_transactions, get_crypto_trigger_orders
from bot.db.user import get_user


async def execute_buy_crypto(ctx, ticker: str, amount: str) -> Dict[str, Any]:
    """Execute crypto buy operation for dashboard buttons"""
    try:
        ticker = ticker.upper()
        user_id = str(ctx.user.id)
        
        # Handle "all" amount
        if amount.lower() == "all":
            user = await get_user(user_id)
            amount_float = float(user.get("points", 0))
            if amount_float < 1.0:
                return {
                    "success": False,
                    "message": "❌ You need at least 1 point to buy cryptocurrency"
                }
        else:
            try:
                amount_float = float(amount)
            except ValueError:
                return {
                    "success": False,
                    "message": "❌ Amount must be a number or 'all'"
                }
        
        # Validate ticker
        if ticker not in CRYPTO_COINS:
            return {
                "success": False,
                "message": f"❌ Unknown cryptocurrency: {ticker}"
            }
        
        if amount_float < 1.0:
            return {
                "success": False,
                "message": "❌ Minimum purchase amount is 1 point"
            }
        
        # Execute purchase
        result = await PortfolioManager.buy_crypto(user_id, ticker, amount_float)
        
        if result["success"]:
            coin_name = CRYPTO_COINS.get(ticker, {}).get('name', ticker)
            return {
                "success": True,
                "message": f"✅ Successfully bought {coin_name} ({ticker})!"
            }
        else:
            return {
                "success": False,
                "message": f"❌ {result['message']}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error processing purchase: {str(e)}"
        }


async def execute_sell_crypto(ctx, ticker: str, amount: str) -> Dict[str, Any]:
    """Execute crypto sell operation for dashboard buttons"""
    try:
        ticker = ticker.upper()
        user_id = str(ctx.user.id)
        
        # Get user's portfolio
        portfolio = get_crypto_portfolio(user_id)
        
        if not portfolio or ticker not in portfolio:
            return {
                "success": False,
                "message": f"❌ You don't own any {ticker}"
            }
        
        user_amount = portfolio[ticker]['amount']
        
        # Handle "all" amount
        if amount.lower() == "all":
            amount_float = user_amount
        else:
            try:
                amount_float = float(amount)
            except ValueError:
                return {
                    "success": False,
                    "message": "❌ Amount must be a number or 'all'"
                }
        
        if amount_float <= 0:
            return {
                "success": False,
                "message": "❌ Sale amount must be greater than 0"
            }
        
        if amount_float > user_amount:
            return {
                "success": False,
                "message": f"❌ You only own {user_amount:.2f} {ticker}"
            }
        
        # Execute sale
        result = await PortfolioManager.sell_crypto(user_id, ticker, amount_float)
        
        if result["success"]:
            coin_name = CRYPTO_COINS.get(ticker, {}).get('name', ticker)
            return {
                "success": True,
                "message": f"✅ Successfully sold {coin_name} ({ticker})!"
            }
        else:
            return {
                "success": False,
                "message": f"❌ {result['message']}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"❌ Error processing sale: {str(e)}"
        }


async def calculate_portfolio_value(portfolio: Dict, prices: Dict) -> tuple:
    """Calculate total portfolio value and P/L"""
    if not portfolio or not prices:
        return 0, 0, 0, 0
    
    total_value = 0
    total_cost = 0
    
    for ticker, data in portfolio.items():
        if data['amount'] > 0:
            current_price = prices.get(ticker, 0)
            value = data['amount'] * current_price
            cost = data['cost_basis']
            
            total_value += value
            total_cost += cost
    
    total_pl = total_value - total_cost
    total_pl_percent = (total_pl / total_cost * 100) if total_cost > 0 else 0
    
    return total_value, total_cost, total_pl, total_pl_percent


async def get_portfolio_pl(user_id: str) -> Dict[str, float]:
    """Get portfolio profit/loss information"""
    portfolio = get_crypto_portfolio(user_id)
    prices = get_crypto_prices()
    
    if not portfolio or not prices:
        return {"all_time_pl": 0, "current_pl": 0}
    
    # Calculate current P/L
    current_pl = 0
    for ticker, data in portfolio.items():
        if data['amount'] > 0:
            current_price = prices.get(ticker, 0)
            value = data['amount'] * current_price
            cost = data['cost_basis']
            current_pl += (value - cost)
    
    # For all-time P/L, we'd need to track transaction history
    # For now, using current P/L as placeholder
    return {
        "all_time_pl": current_pl,
        "current_pl": current_pl
    }


def format_leaderboard_embed() -> discord.Embed:
    """Create leaderboard embed (placeholder - would need real implementation)"""
    embed = discord.Embed(
        title="🏆 Crypto Trading Leaderboard",
        color=0xffd700,
        description="Top crypto traders by all-time profit/loss"
    )
    
    # This would need real implementation to get top traders
    embed.add_field(
        name="💡 Coming Soon",
        value="Leaderboard functionality will be available soon!\nTrack your progress with the Portfolio Dashboard.",
        inline=False
    )
    
    return embed