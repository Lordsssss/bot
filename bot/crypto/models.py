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
                "created_at": datetime.utcnow()
            }
            await crypto_portfolios.insert_one(portfolio)
        return portfolio
    
    @staticmethod
    async def update_portfolio(user_id: str, ticker: str, amount: float, invested_change: float):
        """Update user's portfolio"""
        await crypto_portfolios.update_one(
            {"user_id": user_id},
            {
                "$inc": {
                    f"holdings.{ticker}": amount,
                    "total_invested": invested_change
                }
            },
            upsert=True
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
        """Get crypto portfolio leaderboard"""
        # This will be calculated based on current portfolio value
        portfolios = await crypto_portfolios.find(
            {"holdings": {"$ne": {}}}
        ).to_list(length=None)
        
        # Calculate portfolio values (will be done in the manager)
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