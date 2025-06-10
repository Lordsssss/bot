from bot.db.connection import winners_history

async def record_weekly_winner(user_id, username, points, date):
    await winners_history.insert_one({
        "user_id": user_id,
        "username": username,
        "points": points,
        "date": date,
    })

async def get_winners_history(limit=10):
    cursor = winners_history.find().sort("date", -1).limit(limit)
    return await cursor.to_list(length=limit)
