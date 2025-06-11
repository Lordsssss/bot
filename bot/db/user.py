from bot.db.connection import users

async def get_user(user_id):
    user = await users.find_one({"_id": user_id})
    if not user:
        user = {"_id": user_id, "points": 1000}
        await users.insert_one(user)
    return user

async def update_user_points(user_id, amount):
    await users.update_one({"_id": user_id}, {"$inc": {"points": amount}})

async def check_weekly_limit(user_id, bet_amount):
    user = await get_user(user_id)
    if user["points"] <= 0:
        return False, "Not enough points."
    if user["points"] < bet_amount:
        return False, f"Balance too low: {user['points']} points."

    return True, None
