from motor.motor_asyncio import AsyncIOMotorClient
import os

client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client["betting_bot"]
users = db["users"]
winners_history = db["winners_history"]
