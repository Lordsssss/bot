"""
Trigger orders system for automatic sell orders
"""
from datetime import datetime
from bot.db.connection import db
from bot.crypto.models import CryptoModels
from bot.crypto.portfolio import PortfolioManager

# Collection for trigger orders
trigger_orders = db["trigger_orders"]

async def create_trigger_order(user_id: str, ticker: str, target_gain_percent: float) -> dict:
    """Create a new trigger order based on percentage gain"""
    try:
        # Validate user has the crypto
        portfolio = await CryptoModels.get_user_portfolio(user_id)
        holdings = portfolio.get("holdings", {})
        cost_basis = portfolio.get("cost_basis", {})
        
        if ticker not in holdings or holdings[ticker] <= 0:
            return {
                "success": False,
                "message": f"You don't have any {ticker} to set a trigger for!"
            }
        
        current_holding = holdings[ticker]
        current_cost_basis = cost_basis.get(ticker, 0)
        
        if current_cost_basis <= 0:
            return {
                "success": False,
                "message": f"Cannot determine cost basis for {ticker}. Unable to calculate target price."
            }
        
        # Calculate average purchase price and target price
        avg_purchase_price = current_cost_basis / current_holding
        target_price = avg_purchase_price * (1 + target_gain_percent / 100)
        
        # Get current price for reference
        coin = await CryptoModels.get_coin(ticker)
        current_price = coin["current_price"] if coin else 0
        
        # Create trigger order
        order = {
            "user_id": user_id,
            "ticker": ticker,
            "target_gain_percent": target_gain_percent,
            "trigger_price": target_price,
            "avg_purchase_price": avg_purchase_price,
            "amount": current_holding,  # Sell all holdings when triggered
            "status": "active",  # active, executed, cancelled
            "created_at": datetime.utcnow(),
            "executed_at": None
        }
        
        result = await trigger_orders.insert_one(order)
        order["_id"] = result.inserted_id
        
        return {
            "success": True,
            "message": f"Trigger order created: Sell all {current_holding:.3f} {ticker} when price hits ${target_price:.4f} ({target_gain_percent:+.1f}% gain)",
            "order": order
        }
        
    except Exception as e:
        return {"success": False, "message": f"Error creating trigger order: {str(e)}"}

async def get_user_trigger_orders(user_id: str, status: str = "active") -> list:
    """Get user's trigger orders"""
    try:
        orders = await trigger_orders.find(
            {"user_id": user_id, "status": status}
        ).sort("created_at", -1).to_list(length=None)
        return orders
    except Exception:
        return []

async def cancel_trigger_order(user_id: str, order_id: str) -> dict:
    """Cancel a trigger order"""
    try:
        from bson import ObjectId
        result = await trigger_orders.update_one(
            {"_id": ObjectId(order_id), "user_id": user_id, "status": "active"},
            {"$set": {"status": "cancelled"}}
        )
        
        if result.modified_count > 0:
            return {"success": True, "message": "Trigger order cancelled successfully"}
        else:
            return {"success": False, "message": "Trigger order not found or already processed"}
            
    except Exception as e:
        return {"success": False, "message": f"Error cancelling order: {str(e)}"}

async def check_and_execute_triggers(ticker: str, current_price: float) -> list:
    """Check for trigger orders that should be executed and execute them"""
    executed_orders = []
    
    try:
        # Find all active trigger orders for this ticker where price target has been hit
        orders_to_execute = await trigger_orders.find({
            "ticker": ticker,
            "status": "active",
            "trigger_price": {"$lte": current_price}  # Trigger when current price hits or goes above trigger
        }).to_list(length=None)
        
        for order in orders_to_execute:
            # Get user's current holdings to determine how much to sell
            portfolio = await CryptoModels.get_user_portfolio(order["user_id"])
            holdings = portfolio.get("holdings", {})
            current_holding = holdings.get(ticker, 0)
            
            if current_holding <= 0:
                # Mark as failed - user no longer has this crypto
                await trigger_orders.update_one(
                    {"_id": order["_id"]},
                    {"$set": {"status": "failed", "failure_reason": "No holdings remaining"}}
                )
                continue
            
            # Execute the sell order for all current holdings
            result = await PortfolioManager.sell_crypto(
                order["user_id"], 
                order["ticker"], 
                current_holding  # Sell all current holdings
            )
            
            if result["success"]:
                # Calculate actual gain achieved
                avg_purchase_price = order.get("avg_purchase_price", current_price)
                actual_gain_percent = ((current_price - avg_purchase_price) / avg_purchase_price) * 100
                
                # Mark order as executed
                await trigger_orders.update_one(
                    {"_id": order["_id"]},
                    {
                        "$set": {
                            "status": "executed",
                            "executed_at": datetime.utcnow(),
                            "execution_price": current_price,
                            "actual_gain_percent": actual_gain_percent,
                            "amount_sold": current_holding,
                            "execution_details": result["details"]
                        }
                    }
                )
                
                executed_orders.append({
                    "order": order,
                    "result": result,
                    "execution_price": current_price,
                    "actual_gain_percent": actual_gain_percent,
                    "amount_sold": current_holding
                })
            else:
                # Mark order as failed
                await trigger_orders.update_one(
                    {"_id": order["_id"]},
                    {"$set": {"status": "failed", "failure_reason": result["message"]}}
                )
    
    except Exception as e:
        print(f"Error checking trigger orders: {e}")
    
    return executed_orders

async def get_all_active_triggers() -> dict:
    """Get summary of all active trigger orders by ticker"""
    try:
        pipeline = [
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": "$ticker",
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"},
                "avg_trigger_price": {"$avg": "$trigger_price"}
            }}
        ]
        
        results = await trigger_orders.aggregate(pipeline).to_list(length=None)
        return {result["_id"]: result for result in results}
        
    except Exception:
        return {}

async def cleanup_old_orders(days: int = 30):
    """Clean up old executed/cancelled orders"""
    try:
        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 3600)
        cutoff_datetime = datetime.fromtimestamp(cutoff_date)
        
        result = await trigger_orders.delete_many({
            "status": {"$in": ["executed", "cancelled", "failed"]},
            "created_at": {"$lt": cutoff_datetime}
        })
        
        return result.deleted_count
    except Exception:
        return 0