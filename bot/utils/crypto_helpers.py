"""
Crypto utility functions for common operations
"""
from typing import Dict, List, Any, Optional
from bot.crypto.constants import CRYPTO_COINS, MARKET_EVENTS


def validate_ticker(ticker: str) -> bool:
    """Validate if ticker exists"""
    return ticker.upper() in CRYPTO_COINS


def get_available_tickers() -> List[str]:
    """Get list of available crypto tickers"""
    return list(CRYPTO_COINS.keys())


def get_available_tickers_string() -> str:
    """Get comma-separated string of available tickers"""
    return ", ".join(get_available_tickers())


def validate_amount(amount: float, min_amount: float = 0.001) -> tuple[bool, str]:
    """Validate trading amount"""
    if amount <= 0:
        return False, "Amount must be positive!"
    if amount < min_amount:
        return False, f"Minimum amount is {min_amount}!"
    return True, ""


def get_event_mapping() -> Dict[str, str]:
    """Get mapping of event short names to messages"""
    return {
        "hack": "🚨 BREAKING: Major exchange gets hacked!",
        "elon": "📈 Elon Musk tweets about crypto!",
        "regulation": "🏛️ Government announces crypto regulation!",
        "whale": "🐋 Whale alert: Large transaction detected!",
        "institutional": "📊 Institutional investor enters the market!",
        "congestion": "⚡ Network congestion causes delays!",
        "partnership": "🎉 New partnership announced!",
        "burn": "🔥 Token burn event scheduled!",
        "fud": "😱 FUD spreads on social media!",
        "botmalfunction": "🤖 Trading bot malfunction causes chaos!",
        "crash": "💥 Flash crash detected across markets!",
        "moon": "🚀 Surprise moon mission announcement!",
        "vulnerability": "⚠️ Major security vulnerability discovered!",
        "pump": "🎯 Pump and dump scheme exposed!",
        "diamond": "💎 Diamond hands movement trending!"
    }


def get_available_events() -> List[str]:
    """Get list of available event types"""
    return list(get_event_mapping().keys()) + ["random"]


def find_event_by_message(target_message: str) -> Optional[Dict[str, Any]]:
    """Find event by its message"""
    for event in MARKET_EVENTS:
        if target_message in event["message"]:
            return event
    return None


def calculate_portfolio_summary(portfolio_data: Dict[str, Any]) -> Dict[str, str]:
    """Calculate formatted portfolio summary strings"""
    return {
        "current_value": f"{portfolio_data['total_value']:.2f}",
        "current_invested": f"{portfolio_data['total_invested']:.2f}",
        "current_pl": f"{portfolio_data['profit_loss']:+.2f}",
        "current_pl_percent": f"{portfolio_data['profit_loss_percent']:+.2f}%",
        "all_time_invested": f"{portfolio_data['all_time_invested']:.2f}",
        "all_time_returned": f"{portfolio_data['all_time_returned']:.2f}",
        "all_time_pl": f"{portfolio_data['all_time_profit_loss']:+.2f}",
        "all_time_pl_percent": f"{portfolio_data['all_time_profit_loss_percent']:+.2f}%"
    }


def format_holdings_display(holdings: Dict[str, Dict[str, Any]]) -> str:
    """Format holdings for display"""
    if not holdings:
        return "No crypto holdings yet!\nUse `/crypto buy` to start trading."
    
    holdings_text = ""
    for ticker, holding in holdings.items():
        holdings_text += f"**{ticker}** ({holding['coin_name']})\n"
        holdings_text += f"  Amount: {holding['amount']:.3f}\n"
        holdings_text += f"  Price: ${holding['current_price']:.4f}\n"
        holdings_text += f"  Value: {holding['value']:.2f} points\n\n"
    
    return holdings_text


def format_transaction_history(transactions: List[Dict[str, Any]]) -> str:
    """Format transaction history for display"""
    if not transactions:
        return "No crypto transactions yet! Start trading with `/crypto buy`"
    
    history_text = ""
    for tx in transactions:
        action_emoji = "🟢" if tx["type"] == "buy" else "🔴"
        action = tx["type"].upper()
        time_str = tx["timestamp"].strftime("%m/%d %H:%M")
        
        history_text += f"{action_emoji} **{action}** {tx['amount']:.3f} {tx['ticker']}\n"
        history_text += f"   Price: ${tx['price']:.4f} | Total: {tx['total_cost']:.2f} pts | {time_str}\n\n"
    
    return history_text


def format_leaderboard_entry(position: int, username: str, trader_data: Dict[str, Any]) -> str:
    """Format a single leaderboard entry"""
    from .discord_helpers import get_medal_emoji, get_trading_status_emoji
    
    medal = get_medal_emoji(position)
    status_emoji = get_trading_status_emoji(trader_data['current_holdings'] > 0)
    
    entry = f"{medal} **{username}**\n"
    entry += f"   All-Time P/L: {trader_data['all_time_profit_loss']:+.2f} pts ({trader_data['all_time_profit_loss_percent']:+.2f}%)\n"
    
    if trader_data['current_holdings'] > 0:
        entry += f"   Status: {status_emoji} Active ({trader_data['current_holdings']} holdings)\n\n"
    else:
        entry += f"   Status: {status_emoji} Cashed Out\n\n"
    
    return entry


def determine_affected_coins(event_scope: str, target_coin: str = None) -> List[str]:
    """Determine which coins are affected by an event"""
    import random
    
    if event_scope == "all":
        return get_available_tickers()
    elif event_scope == "random_multiple":
        all_tickers = get_available_tickers()
        num_affected = random.randint(3, min(6, len(all_tickers)))
        return random.sample(all_tickers, num_affected)
    else:  # single
        return [target_coin] if target_coin else [random.choice(get_available_tickers())]


def format_event_details(event: Dict[str, Any], affected_coins: List[str], price_changes: List[Dict[str, Any]] = None) -> str:
    """Format event details for display"""
    if len(affected_coins) == 1:
        if price_changes:
            price_change = price_changes[0]
            return (
                f"**Event:** {event['message']}\n"
                f"**Target Coin:** {affected_coins[0]}\n"
                f"**Impact:** {event['impact']*100:+.1f}%\n"
                f"**Old Price:** ${price_change['old_price']:.4f}\n"
                f"**New Price:** ${price_change['new_price']:.4f}"
            )
        else:
            return (
                f"**Event:** {event['message']}\n"
                f"**Target Coin:** {affected_coins[0]}\n"
                f"**Impact:** {event['impact']*100:+.1f}%"
            )
    elif len(affected_coins) <= 5:
        coins_list = ", ".join(affected_coins)
        return (
            f"**Event:** {event['message']}\n"
            f"**Affected Coins:** {coins_list}\n"
            f"**Impact:** {event['impact']*100:+.1f}% each\n"
            f"**Coins Updated:** {len(price_changes) if price_changes else len(affected_coins)}"
        )
    else:
        return (
            f"**Event:** {event['message']}\n"
            f"**Scope:** Market-wide (ALL coins)\n"
            f"**Impact:** {event['impact']*100:+.1f}% each\n"
            f"**Coins Updated:** {len(price_changes) if price_changes else len(affected_coins)}"
        )