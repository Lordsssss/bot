# Crypto trading constants

# Funny crypto coin names with their tickers
CRYPTO_COINS = {
    "DOGE2": {"name": "DogeCoin 2.0", "description": "Much wow, very profit"},
    "MEME": {"name": "MemeToken", "description": "To the moon! 🚀"},
    "BOOM": {"name": "BoomerCoin", "description": "Back in my day..."},
    "YOLO": {"name": "YoloCoin", "description": "You Only Live Once"},
    "HODL": {"name": "HodlToken", "description": "Diamond hands forever"},
    "REKT": {"name": "RektCoin", "description": "Get rekt or get rich"},
    "PUMP": {"name": "PumpToken", "description": "Number go up"},
    "DUMP": {"name": "DumpCoin", "description": "Gravity is real"},
    "MOON": {"name": "MoonRocket", "description": "Destination: Moon"},
    "Chad": {"name": "ChadCoin", "description": "Alpha energy only"}
}

# Market events that can affect prices
MARKET_EVENTS = [
    {"message": "🚨 BREAKING: Major exchange gets hacked!", "impact": -0.15, "probability": 0.02},
    {"message": "📈 Elon Musk tweets about crypto!", "impact": 0.25, "probability": 0.03},
    {"message": "🏛️ Government announces crypto regulation!", "impact": -0.10, "probability": 0.02},
    {"message": "🐋 Whale alert: Large transaction detected!", "impact": 0.08, "probability": 0.05},
    {"message": "📊 Institutional investor enters the market!", "impact": 0.12, "probability": 0.03},
    {"message": "⚡ Network congestion causes delays!", "impact": -0.08, "probability": 0.04},
    {"message": "🎉 New partnership announced!", "impact": 0.15, "probability": 0.03},
    {"message": "🔥 Token burn event scheduled!", "impact": 0.20, "probability": 0.02},
    {"message": "😱 FUD spreads on social media!", "impact": -0.12, "probability": 0.04},
    {"message": "🤖 Trading bot malfunction causes chaos!", "impact": -0.18, "probability": 0.01}
]

# Volatility ranges
VOLATILITY_RANGES = {
    "low": (0.3, 0.7),
    "normal": (0.8, 1.2),
    "high": (1.3, 2.0),
    "extreme": (2.1, 3.0)
}

# Update frequency (in seconds)
UPDATE_FREQUENCY_MIN = 45  # 45 seconds minimum
UPDATE_FREQUENCY_MAX = 75  # 75 seconds maximum

# Starting price calculation
MAX_STARTING_PRICE = 50.0
MIN_STARTING_PRICE = 0.01

# Transaction fee (in percentage)
TRANSACTION_FEE = 0.001  # 0.1% fee