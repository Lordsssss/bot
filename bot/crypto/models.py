from datetime import datetime
from bot.db.connection import db

# Collections
crypto_coins = db["crypto_coins"]
crypto_prices = db["crypto_prices"]
crypto_portfolios = db["crypto_portfolios"]
crypto_transactions = db["crypto_transactions"]
crypto_events = db["crypto_events"]

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
                "total_invested": 0.0,
                "all_time_invested": 0.0,  # Total ever invested
                "all_time_returned": 0.0,  # Total ever received from sales
                "all_time_profit_loss": 0.0,  # all_time_returned - all_time_invested
                "created_at": datetime.utcnow()
            }
            await crypto_portfolios.insert_one(portfolio)
        return portfolio
    
    @staticmethod
    async def update_portfolio(user_id: str, ticker: str, amount: float, invested_change: float, 
                             is_buy: bool = True, sale_value: float = 0.0):
        """Update user's portfolio with all-time tracking"""
        update_fields = {
            f"holdings.{ticker}": amount,
            "total_invested": invested_change
        }
        
        if is_buy:
            # Buying crypto - add to all_time_invested
            update_fields["all_time_invested"] = invested_change
        else:
            # Selling crypto - add to all_time_returned
            update_fields["all_time_returned"] = sale_value
            # We'll update all_time_profit_loss in a separate operation to avoid recursion
        
        await crypto_portfolios.update_one(
            {"user_id": user_id},
            {"$inc": update_fields},
            upsert=True
        )
        
        # Update all_time_profit_loss separately for sells
        if not is_buy:
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