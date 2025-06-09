from motor.motor_asyncio import AsyncIOMotorClient
import os

mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = mongo_client["betting_bot"]
users = db["users"]

async def get_user(user_id):
    user = await users.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "points": 0}
        await users.insert_one(user)
    return user

async def update_user_points(user_id, amount):
    await users.update_one({"_id": user_id}, {"$inc": {"points": amount}})
