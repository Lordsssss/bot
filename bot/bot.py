"""
Clean, organized main bot file
"""
import os
import discord
from discord.ext import commands
from discord import app_commands

from bot.utils.constants import ALLOWED_CHANNEL_ID
from bot.commands import (
    balance, coinflip, slot, roulette, leaderboard, hall_of_fame,
    next_reset, weekly_limit, my_wins, weekly_reset, force_reset, give, dice,
    server_config, help
)
from bot.commands import crypto
from bot.crypto.manager import CryptoManager

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix="!", intents=intents)


def start_bot():
    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        
        # Start weekly reset task
        weekly_reset.start(client)
        
        # Initialize and start crypto trading system
        crypto_manager = CryptoManager(client)
        await crypto_manager.start()
        
        # Store crypto manager in client for later access
        client.crypto_manager = crypto_manager
        
        # Sync commands
        await client.tree.sync()

    # Register all existing non-crypto commands
    _register_standard_commands()
    
    # Register crypto commands group
    _register_crypto_commands()
    
    # Run the bot
    client.run(os.getenv("DISCORD_TOKEN"))


def _register_standard_commands():
    """Register all standard (non-crypto) commands"""
    client.tree.add_command(help.help_command)
    client.tree.add_command(balance.balance)
    client.tree.add_command(coinflip.coinflip)
    client.tree.add_command(slot.slot)
    client.tree.add_command(roulette.roulette)
    client.tree.add_command(leaderboard.leaderboard)
    client.tree.add_command(hall_of_fame.hall_of_fame)
    client.tree.add_command(next_reset.next_reset)
    client.tree.add_command(weekly_limit.limit)
    client.tree.add_command(my_wins.my_wins)
    client.tree.add_command(force_reset.force_reset)
    client.tree.add_command(give.give)
    client.tree.add_command(dice.dice)
    
    # Server configuration commands
    client.tree.add_command(server_config.config_view)
    client.tree.add_command(server_config.config_language)
    client.tree.add_command(server_config.config_channel_add)
    client.tree.add_command(server_config.config_channel_remove)
    client.tree.add_command(server_config.config_channel_clear)


def _register_crypto_commands():
    """Register crypto commands as a group"""
    crypto_group = app_commands.Group(name="crypto", description="Cryptocurrency trading commands")
    
    # Information commands
    crypto_group.add_command(app_commands.Command(
        name="prices", 
        callback=crypto.crypto_prices, 
        description="View current crypto prices"
    ))
    crypto_group.add_command(app_commands.Command(
        name="charts", 
        callback=crypto.crypto_charts, 
        description="View charts for multiple cryptos at once"
    ))
    crypto_group.add_command(app_commands.Command(
        name="portfolio", 
        callback=crypto.crypto_portfolio, 
        description="View your crypto portfolio"
    ))
    crypto_group.add_command(app_commands.Command(
        name="leaderboard", 
        callback=crypto.crypto_leaderboard, 
        description="View crypto trading leaderboard"
    ))
    crypto_group.add_command(app_commands.Command(
        name="history", 
        callback=crypto.crypto_history, 
        description="View your recent crypto transactions"
    ))
    crypto_group.add_command(app_commands.Command(
        name="analysis", 
        callback=crypto.crypto_analysis, 
        description="View detailed market analysis for skilled trading"
    ))
    
    # Trading commands
    crypto_group.add_command(app_commands.Command(
        name="buy", 
        callback=crypto.crypto_buy, 
        description="Buy cryptocurrency with your points"
    ))
    crypto_group.add_command(app_commands.Command(
        name="sell", 
        callback=crypto.crypto_sell, 
        description="Sell cryptocurrency for points"
    ))
    crypto_group.add_command(app_commands.Command(
        name="sellall", 
        callback=crypto.crypto_sell_all, 
        description="Sell all your cryptocurrency holdings at once"
    ))
    
    # Trigger order commands
    crypto_group.add_command(app_commands.Command(
        name="trigger-set", 
        callback=crypto.crypto_trigger_set, 
        description="Set a trigger order to automatically sell when price hits target"
    ))
    crypto_group.add_command(app_commands.Command(
        name="triggers-list", 
        callback=crypto.crypto_triggers_list, 
        description="List your active trigger orders"
    ))
    crypto_group.add_command(app_commands.Command(
        name="trigger-cancel", 
        callback=crypto.crypto_trigger_cancel, 
        description="Cancel a trigger order"
    ))
    crypto_group.add_command(app_commands.Command(
        name="triggers-market", 
        callback=crypto.crypto_triggers_market, 
        description="[ADMIN] View market-wide trigger order summary"
    ))
    
    # Admin commands
    crypto_group.add_command(app_commands.Command(
        name="adminevent", 
        callback=crypto.crypto_admin_event, 
        description="[ADMIN ONLY] Manually trigger a market event"
    ))
    crypto_group.add_command(app_commands.Command(
        name="adminmigrate", 
        callback=crypto.crypto_admin_migrate, 
        description="[ADMIN ONLY] Run portfolio migration to fix P/L calculations"
    ))
    
    client.tree.add_command(crypto_group)