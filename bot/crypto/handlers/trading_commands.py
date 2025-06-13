"""
Trading commands for crypto (buy, sell, sell all)
"""
import discord
from discord import Interaction
from datetime import datetime

from bot.crypto.portfolio import PortfolioManager
from bot.crypto.constants import TRANSACTION_FEE
from bot.utils.discord_helpers import (
    check_channel_permission, create_embed, send_error_response,
    format_crypto_amount
)
from bot.utils.crypto_helpers import (
    validate_ticker, validate_amount, get_available_tickers_string
)


async def handle_crypto_buy(interaction: Interaction, ticker: str, amount: float):
    """Buy cryptocurrency with points"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        ticker = ticker.upper()
        
        # Validate inputs
        is_valid_amount, amount_error = validate_amount(amount, min_amount=1.0)
        if not is_valid_amount:
            await send_error_response(interaction, amount_error)
            return
        
        if not validate_ticker(ticker):
            await send_error_response(interaction, f"Crypto {ticker} not found!\nAvailable: {get_available_tickers_string()}")
            return
        
        # Execute purchase
        user_id = str(interaction.user.id)
        result = await PortfolioManager.buy_crypto(user_id, ticker, amount)
        
        if result["success"]:
            details = result["details"]
            
            embed = create_embed(
                title="✅ Purchase Successful!",
                description=result["message"],
                color=0x00ff00,
                fields=[{
                    "name": "Transaction Details",
                    "value": (
                        f"**Coins Received:** {format_crypto_amount(details['coins_received'])} {ticker}\n"
                        f"**Price per Coin:** ${details['price_per_coin']:.4f}\n"
                        f"**Total Cost:** {details['total_cost']} points\n"
                        f"**Transaction Fee:** {details['fee']:.2f} points ({TRANSACTION_FEE*100}%)\n"
                        f"**Remaining Points:** {details['remaining_points']:.2f}"
                    ),
                    "inline": False
                }]
            )
            
            await interaction.followup.send(embed=embed)
        else:
            await send_error_response(interaction, result["message"])
            
    except Exception as e:
        await send_error_response(interaction, f"Error processing purchase: {str(e)}")


async def handle_crypto_sell(interaction: Interaction, ticker: str, amount: float):
    """Sell cryptocurrency for points"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        ticker = ticker.upper()
        
        # Validate inputs
        is_valid_amount, amount_error = validate_amount(amount)
        if not is_valid_amount:
            await send_error_response(interaction, amount_error)
            return
        
        if not validate_ticker(ticker):
            await send_error_response(interaction, f"Crypto {ticker} not found!\nAvailable: {get_available_tickers_string()}")
            return
        
        # Execute sale
        user_id = str(interaction.user.id)
        result = await PortfolioManager.sell_crypto(user_id, ticker, amount)
        
        if result["success"]:
            details = result["details"]
            
            embed = create_embed(
                title="✅ Sale Successful!",
                description=result["message"],
                color=0x00ff00,
                fields=[{
                    "name": "Transaction Details",
                    "value": (
                        f"**Coins Sold:** {details['coins_sold']} {ticker}\n"
                        f"**Price per Coin:** ${details['price_per_coin']:.4f}\n"
                        f"**Gross Value:** {details['gross_value']:.2f} points\n"
                        f"**Transaction Fee:** {details['fee']:.2f} points ({TRANSACTION_FEE*100}%)\n"
                        f"**Net Received:** {details['net_value']:.2f} points\n"
                        f"**New Balance:** {details['new_points']:.2f} points"
                    ),
                    "inline": False
                }]
            )
            
            await interaction.followup.send(embed=embed)
        else:
            await send_error_response(interaction, result["message"])
            
    except Exception as e:
        await send_error_response(interaction, f"Error processing sale: {str(e)}")


async def handle_crypto_sell_all(interaction: Interaction):
    """Sell all cryptocurrency holdings at once"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        result = await PortfolioManager.sell_all_crypto(user_id)
        
        if result["success"]:
            details = result["details"]
            
            fields = [{
                "name": "💰 Sale Summary",
                "value": (
                    f"**Total Value:** {details['total_value']:.2f} points\n"
                    f"**Total Fee:** {details['total_fee']:.2f} points\n"
                    f"**Coins Sold:** {details['coins_sold']} different types\n"
                    f"**New Balance:** {details['new_points']:.2f} points"
                ),
                "inline": False
            }]
            
            # Add detailed breakdown if not too many coins
            if len(details['sold_holdings']) <= 8:
                breakdown_text = ""
                for holding in details['sold_holdings']:
                    breakdown_text += f"**{holding['ticker']}:** {format_crypto_amount(holding['amount'])} @ ${holding['price']:.4f} = {holding['value']:.2f} pts\n"
                
                fields.append({
                    "name": "📋 Holdings Sold",
                    "value": breakdown_text if breakdown_text else "No holdings sold",
                    "inline": False
                })
            else:
                fields.append({
                    "name": "📋 Holdings Sold",
                    "value": (
                        f"Sold {len(details['sold_holdings'])} different cryptocurrencies\n"
                        f"Use `/crypto history` to see detailed transaction list"
                    ),
                    "inline": False
                })
            
            embed = create_embed(
                title="✅ Sell All Successful!",
                description=result["message"],
                color=0x00ff00,
                fields=fields
            )
            
            await interaction.followup.send(embed=embed)
        else:
            await send_error_response(interaction, result["message"])
            
    except Exception as e:
        await send_error_response(interaction, f"Error processing sell all: {str(e)}")