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

# Market events that can affect prices (MASSIVE impacts, low frequency)
# Each event specifies its scope: 'single', 'all', or 'random_multiple'
MARKET_EVENTS = [
    # Single coin events (affect only one specific coin)
    {"message": "🚨 BREAKING: Major exchange gets hacked!", "impact": -0.70, "probability": 0.001, "scope": "single"},
    {"message": "🐋 Whale alert: Large transaction detected!", "impact": 0.60, "probability": 0.002, "scope": "single"},
    {"message": "🎉 New partnership announced!", "impact": 0.80, "probability": 0.001, "scope": "single"},
    {"message": "🔥 Token burn event scheduled!", "impact": 1.20, "probability": 0.0005, "scope": "single"},
    {"message": "⚠️ Major security vulnerability discovered!", "impact": -0.95, "probability": 0.0008, "scope": "single"},
    {"message": "🎯 Pump and dump scheme exposed!", "impact": -0.75, "probability": 0.001, "scope": "single"},
    
    # Market-wide events (affect ALL coins)
    {"message": "🏛️ Government announces crypto regulation!", "impact": -0.65, "probability": 0.001, "scope": "all"},
    {"message": "📊 Institutional investor enters the market!", "impact": 0.75, "probability": 0.001, "scope": "all"},
    {"message": "😱 FUD spreads on social media!", "impact": -0.50, "probability": 0.002, "scope": "all"},
    {"message": "🤖 Trading bot malfunction causes chaos!", "impact": -0.85, "probability": 0.001, "scope": "all"},
    {"message": "💥 Flash crash detected across markets!", "impact": -1.50, "probability": 0.0003, "scope": "all"},
    {"message": "💎 Diamond hands movement trending!", "impact": 0.65, "probability": 0.001, "scope": "all"},
    
    # Celebrity/influence events (affect random multiple coins)
    {"message": "📈 Elon Musk tweets about crypto!", "impact": 0.90, "probability": 0.001, "scope": "random_multiple"},
    {"message": "🚀 Surprise moon mission announcement!", "impact": 2.00, "probability": 0.0002, "scope": "random_multiple"},
    {"message": "⚡ Network congestion causes delays!", "impact": -0.55, "probability": 0.002, "scope": "random_multiple"}
]

# Volatility ranges (EXPLOSIVE movements only)
VOLATILITY_RANGES = {
    "low": (3.0, 5.0),
    "normal": (5.1, 8.0),
    "high": (8.1, 12.0),
    "extreme": (12.1, 20.0)
}

# Update frequency (in seconds) - much more frequent
UPDATE_FREQUENCY_MIN = 15  # 15 seconds minimum
UPDATE_FREQUENCY_MAX = 30  # 30 seconds maximum

# Starting price calculation (wider range for more chaos)
MAX_STARTING_PRICE = 100.0
MIN_STARTING_PRICE = 2

# Price floor - coins cannot go below this price
MINIMUM_PRICE_FLOOR = 0.10

# Transaction fee (in percentage) - slightly higher to offset volatility
TRANSACTION_FEE = 0.002  # 0.2% fee

# IRS Investigation settings
IRS_INVESTIGATION_CHANCE = 0.005  # 0.5% chance per transaction
IRS_MIN_PENALTY = 0.40  # Minimum 40% asset seizure
IRS_MAX_PENALTY = 0.90  # Maximum 90% asset seizure