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

# Market events that can affect prices (increased frequency and volatility)
MARKET_EVENTS = [
    {"message": "🚨 BREAKING: Major exchange gets hacked!", "impact": -0.35, "probability": 0.08},
    {"message": "📈 Elon Musk tweets about crypto!", "impact": 0.45, "probability": 0.12},
    {"message": "🏛️ Government announces crypto regulation!", "impact": -0.28, "probability": 0.07},
    {"message": "🐋 Whale alert: Large transaction detected!", "impact": 0.22, "probability": 0.15},
    {"message": "📊 Institutional investor enters the market!", "impact": 0.30, "probability": 0.10},
    {"message": "⚡ Network congestion causes delays!", "impact": -0.20, "probability": 0.12},
    {"message": "🎉 New partnership announced!", "impact": 0.35, "probability": 0.09},
    {"message": "🔥 Token burn event scheduled!", "impact": 0.50, "probability": 0.06},
    {"message": "😱 FUD spreads on social media!", "impact": -0.25, "probability": 0.14},
    {"message": "🤖 Trading bot malfunction causes chaos!", "impact": -0.40, "probability": 0.05},
    {"message": "💥 Flash crash detected across markets!", "impact": -0.60, "probability": 0.03},
    {"message": "🚀 Surprise moon mission announcement!", "impact": 0.80, "probability": 0.02},
    {"message": "⚠️ Major security vulnerability discovered!", "impact": -0.45, "probability": 0.04},
    {"message": "🎯 Pump and dump scheme exposed!", "impact": -0.30, "probability": 0.06},
    {"message": "💎 Diamond hands movement trending!", "impact": 0.25, "probability": 0.10}
]

# Volatility ranges (increased for more chaos)
VOLATILITY_RANGES = {
    "low": (0.8, 1.2),
    "normal": (1.3, 2.0),
    "high": (2.1, 3.5),
    "extreme": (3.6, 5.0)
}

# Update frequency (in seconds) - much more frequent
UPDATE_FREQUENCY_MIN = 15  # 15 seconds minimum
UPDATE_FREQUENCY_MAX = 30  # 30 seconds maximum

# Starting price calculation (wider range for more chaos)
MAX_STARTING_PRICE = 100.0
MIN_STARTING_PRICE = 0.001

# Transaction fee (in percentage) - slightly higher to offset volatility
TRANSACTION_FEE = 0.002  # 0.2% fee