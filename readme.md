# 🎲 Discord Betting Bot

A fully-featured, slash-command-powered Discord bot for weekly betting games, built with `discord.py` and `MongoDB`. Challenge your server members with coin flips, slot machines, and compete for a weekly leaderboard crown!

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Discord](https://img.shields.io/badge/Discord-Bot-7289DA?logo=discord)
![MongoDB](https://img.shields.io/badge/MongoDB-Async-green?logo=mongodb)
![Linted](https://img.shields.io/badge/Code%20Style-Black%20%26%20Ruff-black)

---

## 📁 Project Structure

```
betting_bot/
├── bot/
│   ├── bot.py                 # Entry point
│   ├── commands/              # All slash command modules
│   ├── db/                    # MongoDB models and queries
│   └── utils/                 # Constants and helpers
├── .env                       # Environment variables
├── run.py                     # Bot launcher
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## ⚙️ Features

- 🎰 `/slot` — Try your luck with a slot machine  
- 🪙 `/coinflip` — Bet on heads or tails  
- 💼 `/balance` — Check your current point balance  
- 🏆 `/leaderboard` — See who's on top  
- 🕐 `/nextweek` — Check when the next weekly reset occurs  
- 🔒 `/limit` — Track your weekly betting limit  
- 🏛 `/halloffame` — View the hall of fame of past winners  
- 🥇 `/mywins` — Check how many times you've won

Weekly resets automatically run every **Sunday at midnight UTC**
