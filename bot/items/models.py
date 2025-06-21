"""
Items system database models and operations
"""
from datetime import datetime, timedelta, timezone
from bot.db.connection import db
from bot.items.constants import ITEMS
from bot.db.user import update_user_points

# Collections
user_inventories = db["user_inventories"]
active_effects = db["active_effects"]
item_purchases = db["item_purchases"]

class ItemsManager:
    
    @staticmethod
    async def calculate_user_networth(user_id: str) -> float:
        """Calculate user's total networth (points + crypto holdings value)"""
        try:
            from bot.db.user import get_user
            from bot.crypto.models import CryptoModels
            
            # Get points balance
            user = await get_user(user_id)
            points = user.get("points", 0)
            
            # Get crypto portfolio value
            portfolio = await CryptoModels.get_user_portfolio(user_id)
            holdings = portfolio.get("holdings", {})
            crypto_value = 0
            
            for ticker, amount in holdings.items():
                if amount > 0:
                    coin = await CryptoModels.get_coin(ticker)
                    if coin:
                        crypto_value += amount * coin["current_price"]
            
            return points + crypto_value
            
        except Exception:
            return 0.0
    
    @staticmethod
    async def check_item_cooldown(user_id: str, item_id: str) -> dict:
        """Check if item is on cooldown"""
        try:
            from bot.items.constants import ITEMS
            
            item_def = ITEMS.get(item_id)
            if not item_def:
                return {"on_cooldown": False, "message": "Item not found"}
            
            # Check recent purchases for this item type
            now = datetime.now(timezone.utc)
            cooldown_hours = 24
            cutoff_time = now - timedelta(hours=cooldown_hours)
            
            recent_purchase = await item_purchases.find_one({
                "user_id": user_id,
                "item_id": item_id,
                "purchased_at": {"$gte": cutoff_time}
            }, sort=[("purchased_at", -1)])
            
            if recent_purchase:
                purchased_at = recent_purchase["purchased_at"]
                
                # Handle timezone-naive datetimes from old records
                if purchased_at.tzinfo is None:
                    purchased_at = purchased_at.replace(tzinfo=timezone.utc)
                
                time_since_purchase = now - purchased_at
                remaining_hours = cooldown_hours - (time_since_purchase.total_seconds() / 3600)
                
                if remaining_hours > 0:
                    return {
                        "on_cooldown": True,
                        "remaining_hours": remaining_hours,
                        "message": f"Item on cooldown! You can purchase {item_def['name']} again in {remaining_hours:.1f} hours."
                    }
            
            return {"on_cooldown": False, "message": "Item available for purchase"}
            
        except Exception as e:
            return {"on_cooldown": False, "message": f"Error checking cooldown: {str(e)}"}
    
    @staticmethod
    async def calculate_dynamic_price(item_id: str, user_id: str) -> float:
        """Calculate dynamic price based on user networth for passive income items"""
        try:
            item_def = ITEMS.get(item_id)
            if not item_def:
                return 0
            
            # Non-passive items use fixed price
            if item_def["effect_type"] != "passive_income":
                return item_def.get("price", 0)
            
            # Get base price and user networth
            base_price = item_def.get("base_price", 1000)
            networth = await ItemsManager.calculate_user_networth(user_id)
            
            # Dynamic pricing formula: base_price + (networth * multiplier)
            # Balanced multipliers to ensure profitability
            tier = item_def.get("tier", 1)
            multipliers = {1: 0.005, 2: 0.01, 3: 0.015, 4: 0.02}  # 0.5%, 1%, 1.5%, 2% of networth
            
            multiplier = multipliers.get(tier, 0.05)
            dynamic_price = base_price + (networth * multiplier)
            
            # Ensure minimum price (base price)
            return max(dynamic_price, base_price)
            
        except Exception:
            return item_def.get("base_price", 1000) if item_def else 1000
    
    @staticmethod
    async def get_user_inventory(user_id: str) -> dict:
        """Get user's inventory"""
        inventory = await user_inventories.find_one({"user_id": user_id})
        if not inventory:
            inventory = {
                "user_id": user_id,
                "items": {},
                "total_spent": 0.0,
                "purchases": 0,
                "created_at": datetime.now(timezone.utc)
            }
            await user_inventories.insert_one(inventory)
        return inventory
    
    @staticmethod
    async def purchase_item(user_id: str, item_id: str) -> dict:
        """Purchase an item"""
        try:
            if item_id not in ITEMS:
                return {"success": False, "message": "Item not found!"}
            
            item_def = ITEMS[item_id]
            
            # Check cooldown first
            cooldown_check = await ItemsManager.check_item_cooldown(user_id, item_id)
            if cooldown_check["on_cooldown"]:
                return {"success": False, "message": cooldown_check["message"]}
            
            price = await ItemsManager.calculate_dynamic_price(item_id, user_id)
            
            # Check if user has enough points
            from bot.db.user import get_user
            user = await get_user(user_id)
            current_points = user.get("points", 0)
            
            if current_points < price:
                return {
                    "success": False, 
                    "message": f"Insufficient funds! You have {current_points} points but need {price}."
                }
            
            # Deduct points
            await update_user_points(user_id, -price)
            
            # Add item to inventory
            inventory = await ItemsManager.get_user_inventory(user_id)
            items = inventory.get("items", {})
            items[item_id] = items.get(item_id, 0) + 1
            
            await user_inventories.update_one(
                {"user_id": user_id},
                {
                    "$set": {"items": items},
                    "$inc": {"total_spent": price, "purchases": 1}
                }
            )
            
            # Record purchase
            await item_purchases.insert_one({
                "user_id": user_id,
                "item_id": item_id,
                "price": price,
                "purchased_at": datetime.now(timezone.utc)
            })
            
            return {
                "success": True,
                "message": f"Successfully purchased {item_def['name']} for {price:.0f} points!",
                "item": item_def,
                "actual_price": price,
                "remaining_points": current_points - price
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error purchasing item: {str(e)}"}
    
    @staticmethod
    async def use_item(user_id: str, item_id: str) -> dict:
        """Use/activate an item"""
        try:
            if item_id not in ITEMS:
                return {"success": False, "message": "Item not found!"}
            
            # Check if user has the item
            inventory = await ItemsManager.get_user_inventory(user_id)
            items = inventory.get("items", {})
            
            if items.get(item_id, 0) <= 0:
                return {"success": False, "message": "You don't have this item!"}
            
            item_def = ITEMS[item_id]
            
            # Check if item is already active (for timed items)
            existing_effect = await active_effects.find_one({
                "user_id": user_id,
                "item_id": item_id,
                "active": True
            })
            
            if existing_effect:
                return {"success": False, "message": f"{item_def['name']} is already active!"}
            
            # Remove item from inventory
            items[item_id] -= 1
            if items[item_id] <= 0:
                del items[item_id]
            
            await user_inventories.update_one(
                {"user_id": user_id},
                {"$set": {"items": items}}
            )
            
            # Create active effect
            now = datetime.now(timezone.utc)
            effect = {
                "user_id": user_id,
                "item_id": item_id,
                "effect_type": item_def["effect_type"],
                "effect_value": item_def["effect_value"],
                "active": True,
                "activated_at": now,
                "expires_at": None,
                "uses_remaining": None
            }
            
            # Set expiration or usage limits based on item type
            if item_def["effect_type"] == "trade_boost":
                effect["uses_remaining"] = item_def["duration"]  # Number of trades
            elif "duration" in item_def:
                effect["expires_at"] = now + timedelta(hours=item_def["duration"])
            
            # Add interval for passive income items
            if item_def["effect_type"] == "passive_income":
                effect["next_payout"] = now + timedelta(hours=item_def["effect_interval"])
                effect["effect_interval"] = item_def["effect_interval"]
            
            result = await active_effects.insert_one(effect)
            effect["_id"] = result.inserted_id
            
            return {
                "success": True,
                "message": f"Activated {item_def['name']}!",
                "effect": effect,
                "item": item_def
            }
            
        except Exception as e:
            return {"success": False, "message": f"Error using item: {str(e)}"}
    
    @staticmethod
    async def get_active_cooldowns(user_id: str) -> list:
        """Get all items currently on cooldown for user"""
        try:
            from bot.items.constants import ITEMS
            
            now = datetime.now(timezone.utc)
            cooldown_hours = 24
            cutoff_time = now - timedelta(hours=cooldown_hours)
            
            # Get recent purchases within cooldown period
            recent_purchases = await item_purchases.find({
                "user_id": user_id,
                "purchased_at": {"$gte": cutoff_time}
            }).to_list(length=None)
            
            cooldowns = []
            seen_items = set()
            
            # Sort by purchase time (most recent first) and check each item type once
            for purchase in sorted(recent_purchases, key=lambda x: x["purchased_at"], reverse=True):
                item_id = purchase["item_id"]
                
                if item_id in seen_items:
                    continue
                    
                seen_items.add(item_id)
                item_def = ITEMS.get(item_id)
                
                if item_def:
                    purchased_at = purchase["purchased_at"]
                    
                    # Handle timezone-naive datetimes from old records
                    if purchased_at.tzinfo is None:
                        purchased_at = purchased_at.replace(tzinfo=timezone.utc)
                    
                    time_since_purchase = now - purchased_at
                    remaining_hours = cooldown_hours - (time_since_purchase.total_seconds() / 3600)
                    
                    if remaining_hours > 0:
                        cooldowns.append({
                            "item_id": item_id,
                            "item_name": item_def["name"],
                            "remaining_hours": remaining_hours,
                            "purchased_at": purchase["purchased_at"]
                        })
            
            return cooldowns
            
        except Exception:
            return []
    
    @staticmethod
    async def get_active_effects(user_id: str) -> list:
        """Get user's currently active effects"""
        try:
            now = datetime.now(timezone.utc)
            now_naive = now.replace(tzinfo=None)  # For comparison with old records
            
            # Clean up expired effects - handle both timezone-aware and naive
            await active_effects.update_many(
                {
                    "user_id": user_id,
                    "active": True,
                    "$or": [
                        {"expires_at": {"$lte": now}},
                        {"expires_at": {"$lte": now_naive}},
                        {"uses_remaining": {"$lte": 0}}
                    ]
                },
                {"$set": {"active": False}}
            )
            
            # Get active effects
            effects = await active_effects.find({
                "user_id": user_id,
                "active": True
            }).to_list(length=None)
            
            return effects
            
        except Exception:
            return []
    
    @staticmethod
    async def check_effect_active(user_id: str, effect_type: str) -> dict:
        """Check if user has a specific effect type active"""
        effects = await ItemsManager.get_active_effects(user_id)
        for effect in effects:
            if effect["effect_type"] == effect_type:
                return effect
        return None
    
    @staticmethod
    async def consume_effect_use(user_id: str, effect_type: str) -> bool:
        """Consume one use of an effect (for limited-use items)"""
        try:
            result = await active_effects.update_one(
                {
                    "user_id": user_id,
                    "effect_type": effect_type,
                    "active": True,
                    "uses_remaining": {"$gt": 0}
                },
                {"$inc": {"uses_remaining": -1}}
            )
            
            # Deactivate if no uses remaining
            await active_effects.update_many(
                {
                    "user_id": user_id,
                    "effect_type": effect_type,
                    "active": True,
                    "uses_remaining": {"$lte": 0}
                },
                {"$set": {"active": False}}
            )
            
            return result.modified_count > 0
            
        except Exception:
            return False
    
    @staticmethod
    async def process_passive_income():
        """Process all auto-trader bot payouts"""
        try:
            now = datetime.now(timezone.utc)
            now_naive = now.replace(tzinfo=None)  # For comparison with old records
            
            # Find all active auto-trader bots ready for payout - handle both timezone formats
            ready_bots = await active_effects.find({
                "effect_type": "passive_income",
                "active": True,
                "$or": [
                    {"next_payout": {"$lte": now}},
                    {"next_payout": {"$lte": now_naive}}
                ]
            }).to_list(length=None)
            
            payouts = []
            
            for bot in ready_bots:
                user_id = bot["user_id"]
                effect_value = bot["effect_value"]
                interval_hours = bot["effect_interval"]
                
                # Get user's current balance
                from bot.db.user import get_user
                user = await get_user(user_id)
                current_balance = user.get("points", 0)
                
                # Calculate payout (percentage of balance)
                payout = current_balance * effect_value
                
                if payout > 0:
                    # Give payout
                    await update_user_points(user_id, payout)
                    
                    payouts.append({
                        "user_id": user_id,
                        "amount": payout,
                        "balance_before": current_balance,
                        "balance_after": current_balance + payout
                    })
                
                # Set next payout time
                await active_effects.update_one(
                    {"_id": bot["_id"]},
                    {"$set": {"next_payout": now + timedelta(hours=interval_hours)}}
                )
            
            return payouts
            
        except Exception as e:
            print(f"Error processing passive income: {e}")
            return []
    
    @staticmethod
    async def get_shop_items(user_id: str = None) -> dict:
        """Get all items available in the shop organized by category with dynamic pricing"""
        from bot.items.constants import ITEM_CATEGORIES
        
        shop = {}
        for category, category_name in ITEM_CATEGORIES.items():
            shop[category] = {
                "name": category_name,
                "items": []
            }
        
        for item_id, item_def in ITEMS.items():
            category = item_def.get("category", "other")
            if category in shop:
                item_copy = {
                    "id": item_id,
                    **item_def
                }
                
                # Calculate dynamic price if user_id provided
                if user_id and item_def["effect_type"] == "passive_income":
                    item_copy["price"] = await ItemsManager.calculate_dynamic_price(item_id, user_id)
                    item_copy["is_dynamic"] = True
                else:
                    item_copy["price"] = item_def.get("price", item_def.get("base_price", 0))
                    item_copy["is_dynamic"] = False
                
                shop[category]["items"].append(item_copy)
        
        return shop
    
    @staticmethod
    async def migrate_timezone_records():
        """Migrate timezone-naive datetime records to timezone-aware (one-time utility)"""
        try:
            print("🔄 Migrating timezone-naive datetime records...")
            
            # Update active_effects collection
            effects_updated = await active_effects.update_many(
                {"activated_at": {"$type": "date"}},  # Find datetime fields
                [{"$set": {
                    "activated_at": {"$dateFromString": {"dateString": {"$dateToString": {"date": "$activated_at", "timezone": "UTC"}}}},
                    "expires_at": {"$cond": {
                        "if": {"$ne": ["$expires_at", None]},
                        "then": {"$dateFromString": {"dateString": {"$dateToString": {"date": "$expires_at", "timezone": "UTC"}}}},
                        "else": None
                    }},
                    "next_payout": {"$cond": {
                        "if": {"$ne": ["$next_payout", None]},
                        "then": {"$dateFromString": {"dateString": {"$dateToString": {"date": "$next_payout", "timezone": "UTC"}}}},
                        "else": None
                    }}
                }}]
            )
            
            # Update item_purchases collection
            purchases_updated = await item_purchases.update_many(
                {"purchased_at": {"$type": "date"}},
                [{"$set": {
                    "purchased_at": {"$dateFromString": {"dateString": {"$dateToString": {"date": "$purchased_at", "timezone": "UTC"}}}}
                }}]
            )
            
            # Update user_inventories collection
            inventories_updated = await user_inventories.update_many(
                {"created_at": {"$type": "date"}},
                [{"$set": {
                    "created_at": {"$dateFromString": {"dateString": {"$dateToString": {"date": "$created_at", "timezone": "UTC"}}}}
                }}]
            )
            
            print(f"✅ Migration complete!")
            print(f"   Effects updated: {effects_updated.modified_count}")
            print(f"   Purchases updated: {purchases_updated.modified_count}")
            print(f"   Inventories updated: {inventories_updated.modified_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration error: {e}")
            return False