"""
Trigger orders system for automatic sell orders
"""
from datetime import datetime
from bot.db.connection import db
from bot.crypto.models import CryptoModels
from bot.crypto.portfolio import PortfolioManager

# Collection for trigger orders
trigger_orders = db["trigger_orders"]

async def create_trigger_order(user_id: str, ticker: str, trigger_price: float, amount: float) -> dict:
    """Create a new trigger order"""
    try:
        # Validate user has the crypto to sell
        portfolio = await CryptoModels.get_user_portfolio(user_id)
        holdings = portfolio.get("holdings", {})
        current_holding = holdings.get(ticker, 0)
        
        if current_holding < amount:
            return {
                "success": False,
                "message": f"Insufficient {ticker}! You have {current_holding:.3f} but want to trigger sell {amount}"
            }
        
        # Create trigger order
        order = {
            "user_id": user_id,
            "ticker": ticker,
            "trigger_price": trigger_price,
            "amount": amount,
            "status": "active",  # active, executed, cancelled
            "created_at": datetime.utcnow(),
            "executed_at": None
        }
        
        result = await trigger_orders.insert_one(order)
        order["_id"] = result.inserted_id
        
        return {
            "success": True,
            "message": f"Trigger order created: Sell {amount} {ticker} when price hits ${trigger_price:.4f}",
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
        # Find all active trigger orders for this ticker where price has been hit
        orders_to_execute = await trigger_orders.find({
            "ticker": ticker,
            "status": "active",
            "trigger_price": {"$gte": current_price}  # Trigger when price hits or goes below trigger
        }).to_list(length=None)
        
        for order in orders_to_execute:
            # Execute the sell order
            result = await PortfolioManager.sell_crypto(
                order["user_id"], 
                order["ticker"], 
                order["amount"]
            )
            
            if result["success"]:
                # Mark order as executed
                await trigger_orders.update_one(
                    {"_id": order["_id"]},
                    {
                        "$set": {
                            "status": "executed",
                            "executed_at": datetime.utcnow(),
                            "execution_price": current_price,
                            "execution_details": result["details"]
                        }
                    }
                )
                
                executed_orders.append({
                    "order": order,
                    "result": result,
                    "execution_price": current_price
                })
            else:
                # Mark order as failed (user might not have enough crypto anymore)
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