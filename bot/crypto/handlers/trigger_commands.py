"""
Trigger order commands for automatic selling
"""
import discord
from discord import Interaction
from datetime import datetime

from bot.crypto.trigger_orders import (
    create_trigger_order, get_user_trigger_orders, cancel_trigger_order, get_all_active_triggers
)
from bot.crypto.models import CryptoModels
from bot.utils.discord_helpers import (
    check_channel_permission, create_embed, send_error_response,
    format_crypto_amount
)
from bot.utils.crypto_helpers import (
    validate_ticker, validate_amount, get_available_tickers_string, format_money
)
from bot.db.server_config import get_server_language
from bot.utils.translations import get_text


async def handle_crypto_trigger_set(interaction: Interaction, ticker: str, amount: float, trigger_price: float):
    """Set a trigger order to automatically sell when price hits target"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        ticker = ticker.upper()
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        language = await get_server_language(guild_id)
        
        # Validate inputs
        is_valid_amount, amount_error = validate_amount(amount)
        if not is_valid_amount:
            await send_error_response(interaction, amount_error)
            return
        
        if not validate_ticker(ticker):
            message = get_text(guild_id, "crypto_not_found", language, 
                             ticker=ticker, available=get_available_tickers_string())
            await send_error_response(interaction, message)
            return
        
        if trigger_price <= 0:
            await send_error_response(interaction, "Trigger price must be positive!")
            return
        
        # Get current price for reference
        coin = await CryptoModels.get_coin(ticker)
        if not coin:
            await send_error_response(interaction, f"Crypto {ticker} data not available!")
            return
        
        current_price = coin["current_price"]
        
        # Create trigger order
        result = await create_trigger_order(user_id, ticker, trigger_price, amount)
        
        if result["success"]:
            embed = create_embed(
                title="🎯 Trigger Order Created!",
                description=result["message"],
                color=0x3498db,
                fields=[{
                    "name": "Order Details",
                    "value": (
                        f"**Ticker:** {ticker}\n"
                        f"**Amount:** {format_crypto_amount(amount)} {ticker}\n"
                        f"**Trigger Price:** {format_money(trigger_price)}\n"
                        f"**Current Price:** {format_money(current_price)}\n"
                        f"**Price Difference:** {((trigger_price - current_price) / current_price * 100):+.2f}%"
                    ),
                    "inline": False
                }],
                footer="The order will execute automatically when the price hits your trigger level"
            )
            
            await interaction.followup.send(embed=embed)
        else:
            await send_error_response(interaction, result["message"])
            
    except Exception as e:
        await send_error_response(interaction, f"Error creating trigger order: {str(e)}")


async def handle_crypto_triggers_list(interaction: Interaction):
    """List user's active trigger orders"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        language = await get_server_language(guild_id)
        
        # Get active trigger orders
        triggers = await get_user_trigger_orders(user_id, "active")
        
        if not triggers:
            embed = create_embed(
                title="🎯 Your Trigger Orders",
                description="You have no active trigger orders.\nUse `/crypto trigger-set` to create one!",
                color=0x95a5a6
            )
            await interaction.followup.send(embed=embed)
            return
        
        # Group triggers by ticker for better display
        trigger_text = ""
        total_orders = len(triggers)
        
        for i, trigger in enumerate(triggers, 1):
            ticker = trigger["ticker"]
            amount = trigger["amount"]
            trigger_price = trigger["trigger_price"]
            created = trigger["created_at"].strftime("%m/%d %H:%M")
            
            # Get current price for comparison
            coin = await CryptoModels.get_coin(ticker)
            current_price = coin["current_price"] if coin else 0
            
            price_diff = ((trigger_price - current_price) / current_price * 100) if current_price > 0 else 0
            status_emoji = "🔴" if price_diff > 0 else "🟢"
            
            trigger_text += f"{status_emoji} **{ticker}** - {format_crypto_amount(amount)}\n"
            trigger_text += f"   Trigger: {format_money(trigger_price)} ({price_diff:+.1f}%)\n"
            trigger_text += f"   Created: {created}\n\n"
        
        embed = create_embed(
            title=f"🎯 Your Trigger Orders ({total_orders})",
            description=trigger_text,
            color=0x3498db,
            footer="🟢 = Below trigger | 🔴 = Above trigger | Use /crypto trigger-cancel to remove orders"
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error listing trigger orders: {str(e)}")


async def handle_crypto_trigger_cancel(interaction: Interaction, order_number: int):
    """Cancel a trigger order by number"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        # Get user's active triggers
        triggers = await get_user_trigger_orders(user_id, "active")
        
        if not triggers:
            await send_error_response(interaction, "You have no active trigger orders to cancel!")
            return
        
        if order_number < 1 or order_number > len(triggers):
            await send_error_response(interaction, f"Invalid order number! You have {len(triggers)} active orders.")
            return
        
        # Get the trigger to cancel
        trigger_to_cancel = triggers[order_number - 1]
        order_id = str(trigger_to_cancel["_id"])
        
        # Cancel the order
        result = await cancel_trigger_order(user_id, order_id)
        
        if result["success"]:
            embed = create_embed(
                title="✅ Trigger Order Cancelled",
                description=f"Cancelled trigger order for {trigger_to_cancel['amount']:.3f} {trigger_to_cancel['ticker']} at {format_money(trigger_to_cancel['trigger_price'])}",
                color=0x27ae60
            )
            await interaction.followup.send(embed=embed)
        else:
            await send_error_response(interaction, result["message"])
            
    except Exception as e:
        await send_error_response(interaction, f"Error cancelling trigger order: {str(e)}")


async def handle_crypto_triggers_market(interaction: Interaction):
    """Show market-wide trigger order summary (admin only)"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        # Check if user is admin (simplified check)
        if not interaction.user.guild_permissions.administrator:
            await send_error_response(interaction, "This command requires administrator permissions!")
            return
        
        # Get all active triggers summary
        trigger_summary = await get_all_active_triggers()
        
        if not trigger_summary:
            embed = create_embed(
                title="🎯 Market Trigger Orders",
                description="No active trigger orders in the market.",
                color=0x95a5a6
            )
            await interaction.followup.send(embed=embed)
            return
        
        summary_text = ""
        total_orders = 0
        total_volume = 0
        
        for ticker, data in trigger_summary.items():
            count = data["count"]
            amount = data["total_amount"]
            avg_price = data["avg_trigger_price"]
            
            total_orders += count
            total_volume += amount
            
            summary_text += f"**{ticker}**: {count} orders, {amount:.1f} total, avg trigger {format_money(avg_price)}\n"
        
        embed = create_embed(
            title="🎯 Market Trigger Orders Summary",
            description=summary_text,
            color=0x3498db,
            fields=[{
                "name": "📊 Market Overview",
                "value": f"**Total Orders:** {total_orders}\n**Total Volume:** {total_volume:.1f} coins",
                "inline": False
            }],
            footer="Admin view of all active trigger orders"
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await send_error_response(interaction, f"Error getting market triggers: {str(e)}")