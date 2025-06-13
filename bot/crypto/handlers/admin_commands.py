"""
Admin commands for crypto system (manual events, etc.)
"""
import discord
from discord import Interaction
from datetime import datetime
import random

from bot.crypto.models import CryptoModels
from bot.crypto.constants import MARKET_EVENTS, CRYPTO_COINS
from bot.utils.discord_helpers import (
    check_channel_permission, check_admin_permission, create_embed, 
    send_error_response, get_impact_color
)
from bot.utils.crypto_helpers import (
    get_event_mapping, get_available_events, get_available_tickers_string,
    find_event_by_message, determine_affected_coins, format_event_details,
    validate_ticker
)


async def handle_crypto_admin_event(interaction: Interaction, event_type: str, target_coin: str = None):
    """[ADMIN ONLY] Manually trigger a market event"""
    if not await check_channel_permission(interaction):
        return
    
    if not await check_admin_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        event_type = event_type.lower()
        available_events = get_available_events()
        
        # Validate event type
        if event_type not in available_events:
            events_list = ", ".join(available_events)
            await send_error_response(interaction, f"Invalid event type! Available: {events_list}")
            return
        
        # Select event
        if event_type == "random":
            selected_event = random.choice(MARKET_EVENTS)
        else:
            event_mapping = get_event_mapping()
            target_message = event_mapping.get(event_type)
            if not target_message:
                await send_error_response(interaction, f"Event mapping not found for: {event_type}")
                return
            
            selected_event = find_event_by_message(target_message)
            if not selected_event:
                await send_error_response(interaction, f"Could not find event for: {event_type}")
                return
        
        # Select target coin
        if target_coin:
            target_coin = target_coin.upper()
            if not validate_ticker(target_coin):
                await send_error_response(interaction, f"Invalid coin! Available: {get_available_tickers_string()}")
                return
        else:
            target_coin = random.choice(list(CRYPTO_COINS.keys()))
        
        # Get current coin data
        coin = await CryptoModels.get_coin(target_coin)
        if not coin:
            await send_error_response(interaction, f"Could not find coin data for {target_coin}")
            return
        
        # Determine affected coins and execute event
        event_scope = selected_event.get("scope", "single")
        affected_coins = determine_affected_coins(event_scope, target_coin)
        
        impact = selected_event["impact"]
        price_changes = []
        
        # Apply event to all affected coins
        for affected_ticker in affected_coins:
            affected_coin_data = await CryptoModels.get_coin(affected_ticker)
            if affected_coin_data:
                current_price = affected_coin_data["current_price"]
                new_price = current_price * (1 + impact)
                new_price = max(new_price, 0.001)
                
                await CryptoModels.update_coin_price(affected_ticker, new_price, datetime.utcnow())
                
                price_changes.append({
                    "ticker": affected_ticker,
                    "old_price": current_price,
                    "new_price": new_price
                })
        
        # Record the event
        await CryptoModels.record_market_event(
            message=f"[ADMIN TRIGGERED] {selected_event['message']}",
            impact=impact,
            affected_coins=affected_coins
        )
        
        # Send notification to channel
        if hasattr(interaction.client, 'crypto_manager'):
            fake_event = {
                "message": f"[ADMIN TRIGGERED] {selected_event['message']}",
                "impact": impact,
                "ticker": target_coin,
                "scope": event_scope,
                "affected_coins": affected_coins
            }
            await interaction.client.crypto_manager.send_event_notification(fake_event, coin, affected_coins)
        
        # Send confirmation to admin
        embed = create_embed(
            title="✅ Admin Event Triggered!",
            description="Successfully triggered market event",
            color=get_impact_color(impact),
            fields=[{
                "name": "Event Details",
                "value": format_event_details(selected_event, affected_coins, price_changes),
                "inline": False
            }],
            footer="Event has been broadcast to the channel"
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        await send_error_response(interaction, f"Error triggering event: {str(e)}")