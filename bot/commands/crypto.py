"""
Clean, organized crypto commands using handlers
"""
from discord import app_commands, Interaction

# Import handlers
from bot.crypto.handlers.info_commands import (
    handle_crypto_prices, handle_crypto_charts, handle_crypto_portfolio,
    handle_crypto_leaderboard, handle_crypto_history
)
from bot.crypto.handlers.trading_commands import (
    handle_crypto_buy, handle_crypto_sell, handle_crypto_sell_all
)
from bot.crypto.handlers.admin_commands import handle_crypto_admin_event


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


# Trading Commands
@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    amount="Amount of points to spend"
)
async def crypto_buy(interaction: Interaction, ticker: str, amount: float):
    """Buy cryptocurrency with your points"""
    await handle_crypto_buy(interaction, ticker, amount)


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


# Admin Commands
@app_commands.describe(
    event_type="Type of event to trigger (or 'random' for random event)",
    target_coin="Specific coin to affect (optional, defaults to random)"
)
async def crypto_admin_event(interaction: Interaction, event_type: str, target_coin: str = None):
    """[ADMIN ONLY] Manually trigger a market event"""
    await handle_crypto_admin_event(interaction, event_type, target_coin)