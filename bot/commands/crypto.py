"""
Crypto dashboard system with Discord button integration
"""
from discord import app_commands, Interaction

# Import dashboard views
from bot.crypto.dashboards import PortfolioDashboard, MarketDashboard, TradingDashboard

# Import admin handlers (keeping these as commands)
from bot.crypto.handlers.admin_commands import handle_crypto_admin_event, handle_crypto_admin_migrate
from bot.crypto.handlers.trigger_commands import (
    handle_crypto_trigger_set, handle_crypto_triggers_list, 
    handle_crypto_trigger_cancel, handle_crypto_triggers_market
)


# Dashboard Commands
@app_commands.describe()
async def crypto_portfolio(interaction: Interaction):
    """🏦 Open interactive crypto portfolio dashboard"""
    view = PortfolioDashboard(interaction.user.id, interaction)
    embed = await view._get_portfolio_embed()
    await interaction.response.send_message(embed=embed, view=view)


@app_commands.describe()
async def crypto_market(interaction: Interaction):
    """📊 Open interactive crypto market dashboard"""
    view = MarketDashboard(interaction.user.id, interaction)
    embed = await view._get_market_embed()
    await interaction.response.send_message(embed=embed, view=view)


@app_commands.describe()
async def crypto_trading(interaction: Interaction):
    """⚡ Open advanced crypto trading dashboard"""
    view = TradingDashboard(interaction.user.id, interaction)
    embed = await view._get_trading_embed()
    await interaction.response.send_message(embed=embed, view=view)


# Trigger Order Commands (kept as commands for advanced users)
@app_commands.describe(
    ticker="Crypto ticker symbol (e.g., DOGE2, MEME)",
    target_gain_percent="Target percentage gain to trigger sell (e.g., 25.0 for 25% gain)"
)
async def crypto_trigger_set(interaction: Interaction, ticker: str, target_gain_percent: float):
    """Set a trigger order to automatically sell when achieving target percentage gain"""
    await handle_crypto_trigger_set(interaction, ticker, target_gain_percent)


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