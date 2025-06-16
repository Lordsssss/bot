"""
Clean, organized crypto commands using handlers
"""
from discord import app_commands, Interaction

# Import handlers
from bot.crypto.handlers.info_commands import (
    handle_crypto_prices, handle_crypto_charts, handle_crypto_portfolio,
    handle_crypto_leaderboard, handle_crypto_history, handle_crypto_analysis
)
from bot.crypto.handlers.trading_commands import (
    handle_crypto_buy, handle_crypto_sell, handle_crypto_sell_all
)
from bot.crypto.handlers.trigger_commands import (
    handle_crypto_trigger_set, handle_crypto_triggers_list, 
    handle_crypto_trigger_cancel, handle_crypto_triggers_market
)
from bot.crypto.handlers.admin_commands import handle_crypto_admin_event, handle_crypto_admin_migrate


# Information Commands
@app_commands.describe()
async def crypto_prices(interaction: Interaction):
    """View current crypto prices"""
    await handle_crypto_prices(interaction)


@app_commands.describe(
    ticker="Crypto ticker(s) - single (DOGE2), multiple (DOGE2,MEME), or 'all' for all cryptos",
    timeline="Timeline for chart (e.g., '5m', '1h', '2h', '1d') - defaults to 2h"
)
async def crypto_charts(interaction: Interaction, ticker: str, timeline: str = "2h"):
    """View price chart for one, multiple, or all cryptos with custom timeline"""
    await handle_crypto_charts(interaction, ticker, timeline)


@app_commands.describe()
async def crypto_portfolio(interaction: Interaction):
    """View your crypto portfolio"""
    await handle_crypto_portfolio(interaction)


@app_commands.describe()
async def crypto_leaderboard(interaction: Interaction):
    """View crypto trading leaderboard"""
    await handle_crypto_leaderboard(interaction)


@app_commands.describe()
async def crypto_history(interaction: Interaction):
    """View your recent crypto transactions"""
    await handle_crypto_history(interaction)


@app_commands.describe(
    ticker="Crypto ticker for detailed analysis (optional, shows overview if not provided)"
)
async def crypto_analysis(interaction: Interaction, ticker: str = None):
    """View detailed market analysis for skilled trading"""
    await handle_crypto_analysis(interaction, ticker)


# Trading Commands
@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    amount="Amount of points to spend (or 'all' to spend all available points)",
    trigger_price="Optional: Set automatic sell trigger when price hits this level"
)
async def crypto_buy(interaction: Interaction, ticker: str, amount: str, trigger_price: float = None):
    """Buy cryptocurrency with your points (with optional trigger order)"""
    await handle_crypto_buy(interaction, ticker, amount, trigger_price)


@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    amount="Amount of crypto to sell"
)
async def crypto_sell(interaction: Interaction, ticker: str, amount: float):
    """Sell cryptocurrency for points"""
    await handle_crypto_sell(interaction, ticker, amount)


@app_commands.describe()
async def crypto_sell_all(interaction: Interaction):
    """Sell all your cryptocurrency holdings at once"""
    await handle_crypto_sell_all(interaction)


# Trigger Order Commands
@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    amount="Amount of crypto to sell when triggered",
    trigger_price="Price level that triggers the sell order"
)
async def crypto_trigger_set(interaction: Interaction, ticker: str, amount: float, trigger_price: float):
    """Set a trigger order to automatically sell when price hits target"""
    await handle_crypto_trigger_set(interaction, ticker, amount, trigger_price)


@app_commands.describe()
async def crypto_triggers_list(interaction: Interaction):
    """List your active trigger orders"""
    await handle_crypto_triggers_list(interaction)


@app_commands.describe(
    order_number="Order number to cancel (from /crypto triggers-list)"
)
async def crypto_trigger_cancel(interaction: Interaction, order_number: int):
    """Cancel a trigger order"""
    await handle_crypto_trigger_cancel(interaction, order_number)


@app_commands.describe()
async def crypto_triggers_market(interaction: Interaction):
    """[ADMIN] View market-wide trigger order summary"""
    await handle_crypto_triggers_market(interaction)


# Admin Commands
@app_commands.describe(
    event_type="Type of event to trigger (or 'random' for random event)",
    target_coin="Specific coin to affect (optional, defaults to random)"
)
async def crypto_admin_event(interaction: Interaction, event_type: str, target_coin: str = None):
    """[ADMIN ONLY] Manually trigger a market event"""
    await handle_crypto_admin_event(interaction, event_type, target_coin)


@app_commands.describe()
async def crypto_admin_migrate(interaction: Interaction):
    """[ADMIN ONLY] Run portfolio migration to fix P/L calculations"""
    await handle_crypto_admin_migrate(interaction)