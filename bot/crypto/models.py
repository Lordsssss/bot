from datetime import datetime
from bot.db.connection import db

# Collections
crypto_coins = db["crypto_coins"]
crypto_prices = db["crypto_prices"]
crypto_portfolios = db["crypto_portfolios"]
crypto_transactions = db["crypto_transactions"]
crypto_events = db["crypto_events"]
crypto_weekly_winners = db["crypto_weekly_winners"]

class CryptoModels:
    @staticmethod
    async def get_coin(ticker: str):
        """Get coin data by ticker"""
        return await crypto_coins.find_one({"ticker": ticker})
    
    @staticmethod
    async def get_all_coins():
        """Get all coins"""
        return await crypto_coins.find({}).to_list(length=None)
    
    @staticmethod
    async def update_coin_price(ticker: str, price: float, timestamp: datetime = None):
        """Update coin price and store historical data"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Update current price
        await crypto_coins.update_one(
            {"ticker": ticker},
            {"$set": {"current_price": price, "last_updated": timestamp}}
        )
        
        # Store price history
        await crypto_prices.insert_one({
            "ticker": ticker,
            "price": price,
            "timestamp": timestamp
        })
    
    @staticmethod
    async def get_price_history(ticker: str, hours: int = 24):
        """Get price history for a coin"""
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        cutoff_datetime = datetime.fromtimestamp(cutoff_time)
        
        return await crypto_prices.find({
            "ticker": ticker,
            "timestamp": {"$gte": cutoff_datetime}
        }).sort("timestamp", 1).to_list(length=None)
    
    @staticmethod
    async def get_user_portfolio(user_id: str):
        """Get user's crypto portfolio"""
        portfolio = await crypto_portfolios.find_one({"user_id": user_id})
        if not portfolio:
            # Create empty portfolio
            portfolio = {
                "user_id": user_id,
                "holdings": {},  # {ticker: amount}
                "cost_basis": {},  # {ticker: total_cost} - tracks what was paid for current holdings
                "total_invested": 0.0,  # Current amount invested in holdings
                "all_time_invested": 0.0,  # Total ever invested
                "all_time_returned": 0.0,  # Total ever received from sales
                "all_time_profit_loss": 0.0,  # all_time_returned - all_time_invested
                "created_at": datetime.utcnow()
            }
            await crypto_portfolios.insert_one(portfolio)
        return portfolio
    
    @staticmethod
    async def update_portfolio(user_id: str, ticker: str, amount: float, cost_change: float, 
                             is_buy: bool = True, sale_value: float = 0.0):
        """Update user's portfolio with proper cost basis tracking"""
        
        if is_buy:
            # Buying crypto - add to holdings and cost basis
            update_fields = {
                f"holdings.{ticker}": amount,
                f"cost_basis.{ticker}": cost_change,
                "total_invested": cost_change,
                "all_time_invested": cost_change
            }
            
            await crypto_portfolios.update_one(
                {"user_id": user_id},
                {"$inc": update_fields},
                upsert=True
            )
        else:
            # Selling crypto - need to calculate proportional cost basis reduction
            portfolio = await crypto_portfolios.find_one({"user_id": user_id})
            if not portfolio:
                return
                
            current_holdings = portfolio.get("holdings", {}).get(ticker, 0)
            current_cost_basis = portfolio.get("cost_basis", {}).get(ticker, 0)
            
            if current_holdings <= 0:
                return
                
            # Calculate proportional cost basis to remove
            sell_ratio = abs(amount) / current_holdings
            cost_basis_to_remove = current_cost_basis * sell_ratio
            
            update_fields = {
                f"holdings.{ticker}": amount,  # This should be negative
                f"cost_basis.{ticker}": -cost_basis_to_remove,
                "total_invested": -cost_basis_to_remove,
                "all_time_returned": sale_value
            }
            
            await crypto_portfolios.update_one(
                {"user_id": user_id},
                {"$inc": update_fields},
                upsert=True
            )
            
            # Clean up zero or negative cost basis entries
            updated_portfolio = await crypto_portfolios.find_one({"user_id": user_id})
            if updated_portfolio:
                cost_basis = updated_portfolio.get("cost_basis", {})
                holdings = updated_portfolio.get("holdings", {})
                
                # Remove entries with truly zero holdings (much more conservative)
                unset_fields = {}
                for t, h in holdings.items():
                    if h <= 0.0000001:  # Only remove truly zero holdings (much smaller threshold)
                        unset_fields[f"holdings.{t}"] = ""
                        unset_fields[f"cost_basis.{t}"] = ""
                
                if unset_fields:
                    await crypto_portfolios.update_one(
                        {"user_id": user_id},
                        {"$unset": unset_fields}
                    )
        
        # Update all_time_profit_loss
        portfolio = await crypto_portfolios.find_one({"user_id": user_id})
        if portfolio:
            all_time_invested = portfolio.get("all_time_invested", 0.0)
            all_time_returned = portfolio.get("all_time_returned", 0.0)
            new_all_time_profit_loss = all_time_returned - all_time_invested
            
            await crypto_portfolios.update_one(
                {"user_id": user_id},
                {"$set": {"all_time_profit_loss": new_all_time_profit_loss}}
            )
    
    @staticmethod
    async def record_transaction(user_id: str, ticker: str, transaction_type: str, 
                               amount: float, price: float, total_cost: float, fee: float):
        """Record a crypto transaction"""
        await crypto_transactions.insert_one({
            "user_id": user_id,
            "ticker": ticker,
            "type": transaction_type,  # "buy" or "sell"
            "amount": amount,
            "price": price,
            "total_cost": total_cost,
            "fee": fee,
            "timestamp": datetime.utcnow()
        })
    
    @staticmethod
    async def get_user_transactions(user_id: str, limit: int = 10):
        """Get user's recent transactions"""
        return await crypto_transactions.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(length=None)
    
    @staticmethod
    async def record_market_event(message: str, impact: float, affected_coins: list):
        """Record a market event"""
        await crypto_events.insert_one({
            "message": message,
            "impact": impact,
            "affected_coins": affected_coins,
            "timestamp": datetime.utcnow()
        })
    
    @staticmethod
    async def get_recent_events(hours: int = 1):
        """Get recent market events"""
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        cutoff_datetime = datetime.fromtimestamp(cutoff_time)
        
        return await crypto_events.find({
            "timestamp": {"$gte": cutoff_datetime}
        }).sort("timestamp", -1).to_list(length=None)
    
    @staticmethod
    async def get_portfolio_leaderboard(limit: int = 10):
        """Get crypto portfolio leaderboard based on all-time performance"""
        # Get all portfolios that have ever traded (all_time_invested > 0)
        portfolios = await crypto_portfolios.find(
            {"all_time_invested": {"$gt": 0}}
        ).sort("all_time_profit_loss", -1).limit(limit).to_list(length=None)
        
        return portfolios
    
    @staticmethod
    async def initialize_coin(ticker: str, name: str, description: str, 
                            starting_price: float, trend: float, volatility: float):
        """Initialize a new coin"""
        await crypto_coins.update_one(
            {"ticker": ticker},
            {
                "$set": {
                    "ticker": ticker,
                    "name": name,
                    "description": description,
                    "current_price": starting_price,
                    "starting_price": starting_price,
                    "trend": trend,
                    "daily_volatility": volatility,
                    "last_updated": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    @staticmethod
    async def migrate_portfolios_for_cost_basis():
        """Migrate existing portfolios to include cost basis tracking"""
        portfolios = await crypto_portfolios.find({}).to_list(length=None)
        
        for portfolio in portfolios:
            user_id = portfolio["user_id"]
            
            # Skip if already has cost_basis field
            if "cost_basis" in portfolio:
                continue
                
            print(f"Migrating portfolio for user {user_id}...")
            
            # Calculate cost basis from transaction history
            transactions = await crypto_transactions.find({"user_id": user_id}).to_list(length=None)
            
            # Track holdings and cost basis by coin
            holdings_tracker = {}
            cost_basis_tracker = {}
            all_time_invested = 0.0
            all_time_returned = 0.0
            
            for tx in transactions:
                ticker = tx["ticker"]
                
                if tx["type"] == "buy":
                    amount = tx["amount"]
                    cost = tx["total_cost"]
                    
                    holdings_tracker[ticker] = holdings_tracker.get(ticker, 0) + amount
                    cost_basis_tracker[ticker] = cost_basis_tracker.get(ticker, 0) + cost
                    all_time_invested += cost
                    
                elif tx["type"] == "sell":
                    amount = tx["amount"]
                    sale_value = tx["total_cost"]
                    
                    current_holdings = holdings_tracker.get(ticker, 0)
                    current_cost_basis = cost_basis_tracker.get(ticker, 0)
                    
                    if current_holdings > 0:
                        # Calculate proportional cost basis to remove
                        sell_ratio = min(amount / current_holdings, 1.0)
                        cost_basis_to_remove = current_cost_basis * sell_ratio
                        
                        holdings_tracker[ticker] = max(0, current_holdings - amount)
                        cost_basis_tracker[ticker] = max(0, current_cost_basis - cost_basis_to_remove)
                    
                    all_time_returned += sale_value
            
            # Clean up zero holdings
            holdings_tracker = {k: v for k, v in holdings_tracker.items() if v > 0.001}
            cost_basis_tracker = {k: v for k, v in cost_basis_tracker.items() if k in holdings_tracker}
            
            total_invested = sum(cost_basis_tracker.values())
            all_time_profit_loss = all_time_returned - all_time_invested
            
            # Update portfolio with calculated values
            await crypto_portfolios.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "holdings": holdings_tracker,
                        "cost_basis": cost_basis_tracker,
                        "total_invested": total_invested,
                        "all_time_invested": all_time_invested,
                        "all_time_returned": all_time_returned,
                        "all_time_profit_loss": all_time_profit_loss
                    }
                }
            )
            
            print(f"Migrated portfolio for user {user_id}: holdings={len(holdings_tracker)}, invested=${total_invested:.2f}, P/L=${all_time_profit_loss:.2f}")
    
    @staticmethod
    async def migrate_portfolios_for_all_time_tracking():
        """Migrate existing portfolios to include all-time tracking fields"""
        portfolios = await crypto_portfolios.find({}).to_list(length=None)
        
        for portfolio in portfolios:
            user_id = portfolio["user_id"]
            
            # Skip if already migrated
            if "all_time_invested" in portfolio:
                continue
            
            # Calculate all-time stats from transaction history
            transactions = await crypto_transactions.find({"user_id": user_id}).to_list(length=None)
            
            all_time_invested = 0.0
            all_time_returned = 0.0
            
            for tx in transactions:
                if tx["type"] == "buy":
                    all_time_invested += tx["total_cost"]
                elif tx["type"] == "sell":
                    all_time_returned += tx["total_cost"]
            
            all_time_profit_loss = all_time_returned - all_time_invested
            
            # Update portfolio with calculated values
            await crypto_portfolios.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "all_time_invested": all_time_invested,
                        "all_time_returned": all_time_returned,
                        "all_time_profit_loss": all_time_profit_loss
                    }
                }
            )
            
            print(f"Migrated portfolio for user {user_id}: invested={all_time_invested:.2f}, returned={all_time_returned:.2f}, P/L={all_time_profit_loss:.2f}")
    
    @staticmethod
    async def record_weekly_crypto_winner(user_id: str, username: str, weekly_pnl: float, 
                                        portfolio_value: float, best_coin: str, best_coin_pnl: float, date: str):
        """Record weekly crypto winner"""
        await crypto_weekly_winners.insert_one({
            "user_id": user_id,
            "username": username,
            "weekly_pnl": weekly_pnl,
            "portfolio_value": portfolio_value,
            "best_coin": best_coin,
            "best_coin_pnl": best_coin_pnl,
            "date": date,
            "timestamp": datetime.utcnow()
        })
    
    @staticmethod
    async def get_crypto_weekly_winners(limit: int = 10):
        """Get crypto weekly winners history"""
        return await crypto_weekly_winners.find().sort("date", -1).limit(limit).to_list(length=None)
    
    @staticmethod
    async def reset_crypto_system():
        """Complete reset of crypto system for weekly reset"""
        # Clear all portfolios
        await crypto_portfolios.delete_many({})
        
        # Clear all transactions
        await crypto_transactions.delete_many({})
        
        # Clear all price history
        await crypto_prices.delete_many({})
        
        # Clear all market events
        await crypto_events.delete_many({})
        
        # Reset all coins to starting prices
        coins = await crypto_coins.find({}).to_list(length=None)
        for coin in coins:
            if "starting_price" in coin:
                await crypto_coins.update_one(
                    {"ticker": coin["ticker"]},
                    {
                        "$set": {
                            "current_price": coin["starting_price"],
                            "last_updated": datetime.utcnow()
                        }
                    }
                )
        
        print("Crypto system reset complete: portfolios, transactions, prices, and events cleared; coins reset to starting prices")
    
    @staticmethod
    async def get_weekly_crypto_leaderboard():
        """Get current week's crypto P/L leaderboard"""
        # Get all portfolios with positive all_time_profit_loss
        portfolios = await crypto_portfolios.find(
            {"all_time_profit_loss": {"$ne": 0}}
        ).sort("all_time_profit_loss", -1).to_list(length=None)
        
        return portfolios


# Wrapper functions for dashboard compatibility
async def get_crypto_portfolio(user_id: str):
    """Async wrapper for getting user portfolio - returns simplified format"""
    portfolio = await CryptoModels.get_user_portfolio(user_id)
    if not portfolio:
        return {}
    
    # Convert to simplified format: {ticker: {amount: float, cost_basis: float}}
    simplified = {}
    holdings = portfolio.get("holdings", {})
    cost_basis = portfolio.get("cost_basis", {})
    
    for ticker, amount in holdings.items():
        if amount > 0:
            simplified[ticker] = {
                "amount": amount,
                "cost_basis": cost_basis.get(ticker, 0)
            }
    
    return simplified


async def get_crypto_prices():
    """Async wrapper for getting current crypto prices"""
    coins = await CryptoModels.get_all_coins()
    prices = {}
    for coin in coins:
        prices[coin["ticker"]] = coin.get("current_price", 0.0)
    return prices


async def get_crypto_transactions(user_id: str, limit: int = 10):
    """Async wrapper for getting user transactions"""
    transactions = await CryptoModels.get_user_transactions(user_id, limit)
    # Convert to simplified format
    simplified = []
    for tx in transactions:
        simplified.append({
            "ticker": tx["ticker"],
            "action": tx["type"],  # "buy" or "sell"
            "amount": tx["amount"],
            "price": tx["price"],
            "timestamp": tx["timestamp"].strftime("%Y-%m-%d %H:%M")
        })
    return simplified


async def get_crypto_trigger_orders(user_id: str):
    """Async wrapper for getting user trigger orders"""
    from bot.crypto.trigger_orders import get_user_trigger_orders
    
    try:
        orders = await get_user_trigger_orders(user_id, "active")
        return orders
    except Exception as e:
        print(f"Error getting trigger orders: {e}")
        return []