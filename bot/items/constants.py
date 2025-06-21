"""
Items constants and definitions
"""

# Item definitions with their properties
ITEMS = {
    "market_insider_tip": {
        "name": "📊 Market Insider Tip",
        "description": "Get exclusive market intel! Next 3 crypto trades have 15% better win odds.",
        "price": 2500,
        "duration": 3,  # Number of trades affected
        "effect_type": "trade_boost",
        "effect_value": 0.15,  # 15% better odds
        "emoji": "📊",
        "category": "trading"
    },
    "underpaid_immigrant": {
        "name": "👷 Underpaid Immigrant",
        "description": "Works harder than anyone for scraps! Poor guy doesn't even know what Bitcoin is but somehow makes you money. 0.3% every 6h for 24h.",
        "base_price": 200,
        "duration": 24,  # Hours active
        "effect_type": "passive_income",
        "effect_value": 0.003,  # 0.3% per cycle
        "effect_interval": 6,  # Hours between payouts
        "emoji": "👷",
        "category": "passive",
        "tier": 1
    },
    "goldman_intern": {
        "name": "🤓 Coked Up Goldman Intern", 
        "description": "Three espressos and daddy's connections! Makes questionable trades at 3 AM but somehow beats the market. 0.6% every 6h for 24h.",
        "base_price": 500,
        "duration": 24,  # Hours active
        "effect_type": "passive_income",
        "effect_value": 0.006,  # 0.6% per cycle
        "effect_interval": 6,  # Hours between payouts
        "emoji": "🤓",
        "category": "passive",
        "tier": 2
    },
    "crypto_influencer": {
        "name": "🎭 Crypto Influencer",
        "description": "Master of the rug pull! Will shill your bags while secretly dumping his own. Not financial advice! 1.0% every 6h for 24h.",
        "base_price": 1000,
        "duration": 24,  # Hours active
        "effect_type": "passive_income", 
        "effect_value": 0.01,  # 1.0% per cycle
        "effect_interval": 6,  # Hours between payouts
        "emoji": "🎭",
        "category": "passive",
        "tier": 3
    },
    "sam_bankman_fried": {
        "name": "👨‍💼 Sam Bankman-Fried",
        "description": "It's not fraud, it's 'effective altruism'! Will trade your mom's retirement fund to infinity and beyond. 1.5% every 6h for 24h.",
        "base_price": 2000,
        "duration": 24,  # Hours active
        "effect_type": "passive_income",
        "effect_value": 0.015,  # 1.5% per cycle
        "effect_interval": 6,  # Hours between payouts
        "emoji": "👨‍💼",
        "category": "passive",
        "tier": 4
    },
    "lucky_charm": {
        "name": "🍀 Lucky Charm",
        "description": "Fortune favors you! +15% win odds in all casino games for 24 hours.",
        "price": 3000,
        "duration": 24,  # Hours active
        "effect_type": "casino_boost",
        "effect_value": 0.15,  # 15% better odds
        "emoji": "🍀",
        "category": "gambling"
    },
    "tax_evasion_license": {
        "name": "💰 Tax Evasion License",
        "description": "Avoid the taxman! Removes all transaction fees and IRS investigations for 24h.",
        "price": 4000,
        "duration": 24,  # Hours active
        "effect_type": "fee_immunity",
        "effect_value": 1.0,  # 100% fee reduction
        "emoji": "💰",
        "category": "trading"
    }
}

# Item categories for organization
ITEM_CATEGORIES = {
    "trading": "📈 Trading Items",
    "passive": "🤖 Passive Income",
    "gambling": "🎰 Casino Items"
}

# Effect types for easy reference
EFFECT_TYPES = {
    "trade_boost": "Improves trading win odds",
    "passive_income": "Generates automatic income",
    "casino_boost": "Improves casino game odds", 
    "fee_immunity": "Removes fees and penalties"
}