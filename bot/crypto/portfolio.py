from datetime import datetime
from .models import CryptoModels
from .constants import TRANSACTION_FEE
from bot.db.user import get_user, update_user_points

class PortfolioManager:
    @staticmethod
    async def buy_crypto(user_id: str, ticker: str, amount_to_spend: float) -> dict:
        """
        Buy cryptocurrency with points
        Returns: dict with success status and details
        """
        try:
            # Get user's current points
            user = await get_user(user_id)
            current_points = user.get("points", 0)
            
            # Check if user has enough points
            if current_points < amount_to_spend:
                return {
                    "success": False,
                    "message": f"Insufficient funds! You have {current_points} points but need {amount_to_spend}."
                }
            
            # Get coin data
            coin = await CryptoModels.get_coin(ticker)
            if not coin:
                return {
                    "success": False,
                    "message": f"Crypto {ticker} not found!"
                }
            
            current_price = coin["current_price"]
            
            # Calculate transaction fee
            fee = amount_to_spend * TRANSACTION_FEE
            amount_after_fee = amount_to_spend - fee
            
            # Calculate how many coins user gets (rounded to 3 decimal places)
            coins_received = round(amount_after_fee / current_price, 3)
            
            # Update user's points (deduct the spent amount)
            await update_user_points(user_id, -amount_to_spend)
            
            # Update user's portfolio
            await CryptoModels.update_portfolio(
                user_id=user_id,
                ticker=ticker,
                amount=coins_received,
                invested_change=amount_to_spend,
                is_buy=True
            )
            
            # Record transaction
            await CryptoModels.record_transaction(
                user_id=user_id,
                ticker=ticker,
                transaction_type="buy",
                amount=coins_received,
                price=current_price,
                total_cost=amount_to_spend,
                fee=fee
            )
            
            return {
                "success": True,
                "message": f"Successfully bought {coins_received:.3f} {ticker} for {amount_to_spend} points!",
                "details": {
                    "coins_received": coins_received,
                    "price_per_coin": current_price,
                    "total_cost": amount_to_spend,
                    "fee": fee,
                    "remaining_points": current_points - amount_to_spend
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error buying crypto: {str(e)}"
            }
    
    @staticmethod
    async def sell_crypto(user_id: str, ticker: str, amount_to_sell: float) -> dict:
        """
        Sell cryptocurrency for points
        Returns: dict with success status and details
        """
        try:
            # Get user's portfolio
            portfolio = await CryptoModels.get_user_portfolio(user_id)
            holdings = portfolio.get("holdings", {})
            
            # Check if user has enough of this crypto
            current_holding = holdings.get(ticker, 0)
            if current_holding < amount_to_sell:
                return {
                    "success": False,
                    "message": f"Insufficient {ticker}! You have {current_holding:.3f} but want to sell {amount_to_sell}."
                }
            
            # Get coin data
            coin = await CryptoModels.get_coin(ticker)
            if not coin:
                return {
                    "success": False,
                    "message": f"Crypto {ticker} not found!"
                }
            
            current_price = coin["current_price"]
            
            # Calculate sale value
            gross_sale_value = amount_to_sell * current_price
            fee = gross_sale_value * TRANSACTION_FEE
            net_sale_value = gross_sale_value - fee
            
            # Update user's points (add the sale proceeds)
            await update_user_points(user_id, net_sale_value)
            
            # Update user's portfolio (remove the sold coins)
            await CryptoModels.update_portfolio(
                user_id=user_id,
                ticker=ticker,
                amount=-amount_to_sell,
                invested_change=-net_sale_value,  # Negative because we're getting money back
                is_buy=False,
                sale_value=net_sale_value
            )
            
            # Record transaction
            await CryptoModels.record_transaction(
                user_id=user_id,
                ticker=ticker,
                transaction_type="sell",
                amount=amount_to_sell,
                price=current_price,
                total_cost=net_sale_value,
                fee=fee
            )
            
            # Get updated user points
            updated_user = await get_user(user_id)
            new_points = updated_user.get("points", 0)
            
            return {
                "success": True,
                "message": f"Successfully sold {amount_to_sell} {ticker} for {net_sale_value:.2f} points!",
                "details": {
                    "coins_sold": amount_to_sell,
                    "price_per_coin": current_price,
                    "gross_value": gross_sale_value,
                    "fee": fee,
                    "net_value": net_sale_value,
                    "new_points": new_points
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error selling crypto: {str(e)}"
            }
    
    @staticmethod
    async def sell_all_crypto(user_id: str) -> dict:
        """
        Sell all cryptocurrency holdings for points
        Returns: dict with success status and details
        """
        try:
            # Get user's portfolio
            portfolio = await CryptoModels.get_user_portfolio(user_id)
            holdings = portfolio.get("holdings", {})
            
            if not holdings or all(amount <= 0 for amount in holdings.values()):
                return {
                    "success": False,
                    "message": "No crypto holdings to sell!"
                }
            
            total_sale_value = 0
            total_fee = 0
            sold_coins = []
            
            # Sell each holding
            for ticker, amount in holdings.items():
                if amount > 0:  # Only sell positive holdings
                    # Get coin data
                    coin = await CryptoModels.get_coin(ticker)
                    if not coin:
                        continue
                    
                    current_price = coin["current_price"]
                    
                    # Calculate sale value
                    gross_sale_value = amount * current_price
                    fee = gross_sale_value * TRANSACTION_FEE
                    net_sale_value = gross_sale_value - fee
                    
                    total_sale_value += net_sale_value
                    total_fee += fee
                    
                    # Update user's portfolio (remove all coins)
                    await CryptoModels.update_portfolio(
                        user_id=user_id,
                        ticker=ticker,
                        amount=-amount,
                        invested_change=-net_sale_value,
                        is_buy=False,
                        sale_value=net_sale_value
                    )
                    
                    # Record transaction
                    await CryptoModels.record_transaction(
                        user_id=user_id,
                        ticker=ticker,
                        transaction_type="sell",
                        amount=amount,
                        price=current_price,
                        total_cost=net_sale_value,
                        fee=fee
                    )
                    
                    sold_coins.append({
                        "ticker": ticker,
                        "amount": round(amount, 3),
                        "price": current_price,
                        "value": net_sale_value
                    })
            
            if not sold_coins:
                return {
                    "success": False,
                    "message": "No valid crypto holdings found to sell!"
                }
            
            # Update user's points (add the sale proceeds)
            await update_user_points(user_id, total_sale_value)
            
            # Get updated user points
            updated_user = await get_user(user_id)
            new_points = updated_user.get("points", 0)
            
            return {
                "success": True,
                "message": f"Successfully sold all crypto for {total_sale_value:.2f} points!",
                "details": {
                    "total_value": total_sale_value,
                    "total_fee": total_fee,
                    "coins_sold": len(sold_coins),
                    "new_points": new_points,
                    "sold_holdings": sold_coins
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error selling all crypto: {str(e)}"
            }
    
    @staticmethod
    async def get_portfolio_value(user_id: str) -> dict:
        """
        Calculate current portfolio value
        Returns: dict with portfolio details
        """
        try:
            portfolio = await CryptoModels.get_user_portfolio(user_id)
            holdings = portfolio.get("holdings", {})
            total_invested = portfolio.get("total_invested", 0)
            
            # All-time stats
            all_time_invested = portfolio.get("all_time_invested", 0)
            all_time_returned = portfolio.get("all_time_returned", 0)
            all_time_profit_loss = portfolio.get("all_time_profit_loss", 0)
            
            if not holdings and all_time_invested == 0:
                return {
                    "total_value": 0,
                    "total_invested": 0,
                    "profit_loss": 0,
                    "profit_loss_percent": 0,
                    "holdings": {},
                    "all_time_invested": 0,
                    "all_time_returned": 0,
                    "all_time_profit_loss": 0,
                    "all_time_profit_loss_percent": 0
                }
            
            total_current_value = 0
            detailed_holdings = {}
            
            # Calculate current value of each holding
            for ticker, amount in holdings.items():
                if amount > 0:  # Only include positive holdings
                    coin = await CryptoModels.get_coin(ticker)
                    if coin:
                        current_price = coin["current_price"]
                        holding_value = amount * current_price
                        total_current_value += holding_value
                        
                        detailed_holdings[ticker] = {
                            "amount": round(amount, 3),
                            "current_price": current_price,
                            "value": holding_value,
                            "coin_name": coin["name"]
                        }
            
            # Calculate current profit/loss
            profit_loss = total_current_value - total_invested
            profit_loss_percent = (profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            # Calculate all-time profit/loss including current holdings
            current_portfolio_value = total_current_value
            total_all_time_value = all_time_returned + current_portfolio_value
            all_time_profit_loss_with_current = total_all_time_value - all_time_invested
            all_time_profit_loss_percent = (all_time_profit_loss_with_current / all_time_invested * 100) if all_time_invested > 0 else 0
            
            return {
                "total_value": total_current_value,
                "total_invested": total_invested,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
                "holdings": detailed_holdings,
                "all_time_invested": all_time_invested,
                "all_time_returned": all_time_returned,
                "all_time_profit_loss": all_time_profit_loss_with_current,
                "all_time_profit_loss_percent": all_time_profit_loss_percent
            }
            
        except Exception as e:
            return {
                "total_value": 0,
                "total_invested": 0,
                "profit_loss": 0,
                "profit_loss_percent": 0,
                "holdings": {},
                "all_time_invested": 0,
                "all_time_returned": 0,
                "all_time_profit_loss": 0,
                "all_time_profit_loss_percent": 0,
                "error": str(e)
            }
    
    @staticmethod
    async def get_leaderboard(limit: int = 10) -> list:
        """
        Get crypto trading leaderboard based on profit/loss percentage
        """
        try:
            # Get all portfolios sorted by all-time profit/loss
            portfolios = await CryptoModels.get_portfolio_leaderboard(limit)
            
            leaderboard = []
            
            for portfolio in portfolios:
                user_id = portfolio["user_id"]
                portfolio_data = await PortfolioManager.get_portfolio_value(user_id)
                
                if portfolio_data["all_time_invested"] > 0:  # Only include users who have ever invested
                    leaderboard.append({
                        "user_id": user_id,
                        "total_value": portfolio_data["total_value"],
                        "all_time_invested": portfolio_data["all_time_invested"],
                        "all_time_returned": portfolio_data["all_time_returned"],
                        "all_time_profit_loss": portfolio_data["all_time_profit_loss"],
                        "all_time_profit_loss_percent": portfolio_data["all_time_profit_loss_percent"],
                        "current_holdings": len(portfolio_data["holdings"])
                    })
            
            # Already sorted by database query, but ensure by all-time profit/loss
            leaderboard.sort(key=lambda x: x["all_time_profit_loss"], reverse=True)
            
            return leaderboard[:limit]
            
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []