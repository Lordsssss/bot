from motor.motor_asyncio import AsyncIOMotorClient
import os

mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo_client["betting_bot"]
users = db["users"]

# Create a new collection for winner history
winners_history = db["winners_history"]

async def get_user(user_id):
    user = await users.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "points": 0}
        await users.insert_one(user)
    return user

async def update_user_points(user_id, amount):
    await users.update_one({"_id": user_id}, {"$inc": {"points": amount}})

async def check_and_update_daily_usage(user_id, game_name):
    """
    Checks if user can use the game today, updates timestamp if allowed
    Returns: True if user can play today, False if already played today
    """
    from datetime import datetime
    
    user = await get_user(user_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Check if user has already played this game today
    last_used = user.get("last_used", {}).get(game_name, "")
    
    if last_used == today:
        # User already used this game today
        return False
    
    # User hasn't used the game today, update timestamp
    await users.update_one(
        {"_id": user_id},
        {"$set": {f"last_used.{game_name}": today}}
    )
    return True

async def record_weekly_winner(user_id, username, points, date):
    """Store a record of the weekly winner"""
    await winners_history.insert_one({
        "user_id": user_id,
        "username": username,
        "points": points,
        "date": date
    })

async def get_winners_history(limit=10):
    """Retrieve past winners, most recent first"""
    cursor = winners_history.find().sort("date", -1).limit(limit)
    return await cursor.to_list(length=limit)
