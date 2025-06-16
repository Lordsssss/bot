"""
Trading commands for crypto (buy, sell, sell all)
"""
import discord
from discord import Interaction
from datetime import datetime

from bot.crypto.portfolio import PortfolioManager
from bot.crypto.constants import TRANSACTION_FEE, IRS_INVESTIGATION_CHANCE
from bot.utils.discord_helpers import (
    check_channel_permission, create_embed, send_error_response,
    format_crypto_amount
)
from bot.utils.crypto_helpers import (
    validate_ticker, validate_amount, get_available_tickers_string,
    format_money, trigger_irs_investigation
)
from bot.db.user import get_user, update_user_points
import random


async def handle_crypto_buy(interaction: Interaction, ticker: str, amount: str):
    """Buy cryptocurrency with points"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        ticker = ticker.upper()
        user_id = str(interaction.user.id)
        
        # Handle "all" amount
        if amount.lower() == "all":
            user = await get_user(user_id)
            amount_float = float(user.get("points", 0))
            if amount_float < 1.0:
                await send_error_response(interaction, "You need at least 1 point to buy crypto!")
                return
        else:
            try:
                amount_float = float(amount)
            except ValueError:
                await send_error_response(interaction, "Amount must be a number or 'all'!")
                return
        
        # Validate inputs
        is_valid_amount, amount_error = validate_amount(amount_float, min_amount=1.0)
        if not is_valid_amount:
            await send_error_response(interaction, amount_error)
            return
        
        if not validate_ticker(ticker):
            await send_error_response(interaction, f"Crypto {ticker} not found!\nAvailable: {get_available_tickers_string()}")
            return
        
        # Check for IRS investigation BEFORE purchase
        irs_investigation = None
        if random.random() < IRS_INVESTIGATION_CHANCE:
            irs_investigation = trigger_irs_investigation()
        
        # Execute purchase
        result = await PortfolioManager.buy_crypto(user_id, ticker, amount_float)
        
        if result["success"]:
            details = result["details"]
            
            # If IRS investigation triggered, apply penalty AFTER successful purchase
            if irs_investigation:
                penalty_percent = irs_investigation["penalty_percent"]
                
                # Get current user state after purchase
                user = await get_user(user_id)
                current_points = user.get("points", 0)
                
                # Get portfolio to calculate crypto value
                from bot.crypto.models import CryptoModels
                portfolio = await CryptoModels.get_user_portfolio(user_id)
                total_crypto_value = 0
                
                holdings = portfolio.get("holdings", {})
                for hold_ticker, hold_amount in holdings.items():
                    coin = await CryptoModels.get_coin(hold_ticker)
                    if coin:
                        total_crypto_value += hold_amount * coin["current_price"]
                
                # Calculate penalties
                points_penalty = current_points * penalty_percent
                crypto_penalty_percent = penalty_percent
                
                # Apply points penalty
                await update_user_points(user_id, -points_penalty)
                
                # Apply crypto penalty by reducing all holdings
                for hold_ticker, hold_amount in holdings.items():
                    new_amount = hold_amount * (1 - crypto_penalty_percent)
                    amount_to_remove = hold_amount - new_amount
                    
                    # Update portfolio to remove crypto
                    await CryptoModels.update_portfolio(
                        user_id=user_id,
                        ticker=hold_ticker,
                        amount=-amount_to_remove,
                        cost_change=0,
                        is_buy=False,
                        sale_value=0  # IRS seizure, no sale value
                    )
                
                # Send IRS investigation embed
                irs_embed = create_embed(
                    title="🚨 IRS INVESTIGATION!",
                    description=irs_investigation["message"],
                    color=0xff0000,
                    fields=[{
                        "name": "💸 Assets Seized",
                        "value": (
                            f"**Points Lost:** {format_money(points_penalty)}\n"
                            f"**Crypto Reduced:** {penalty_percent*100:.1f}% of all holdings\n"
                            f"**Total Value Lost:** ~{format_money(points_penalty + (total_crypto_value * penalty_percent))}"
                        ),
                        "inline": False
                    }]
                )
                await interaction.followup.send(embed=irs_embed)
                
                # Update remaining points in details
                updated_user = await get_user(user_id)
                details["remaining_points"] = updated_user.get("points", 0)
            
            embed = create_embed(
                title="✅ Purchase Successful!",
                description=result["message"],
                color=0x00ff00,
                fields=[{
                    "name": "Transaction Details",
                    "value": (
                        f"**Coins Received:** {format_crypto_amount(details['coins_received'])} {ticker}\n"
                        f"**Price per Coin:** {format_money(details['price_per_coin'])}\n"
                        f"**Total Cost:** {format_money(details['total_cost'])}\n"
                        f"**Transaction Fee:** {format_money(details['fee'])} ({TRANSACTION_FEE*100}%)\n"
                        f"**Remaining Points:** {format_money(details['remaining_points'])}"
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
        user_id = str(interaction.user.id)
        
        # Validate inputs
        is_valid_amount, amount_error = validate_amount(amount)
        if not is_valid_amount:
            await send_error_response(interaction, amount_error)
            return
        
        if not validate_ticker(ticker):
            await send_error_response(interaction, f"Crypto {ticker} not found!\nAvailable: {get_available_tickers_string()}")
            return
        
        # Check for IRS investigation BEFORE sale
        irs_investigation = None
        if random.random() < IRS_INVESTIGATION_CHANCE:
            irs_investigation = trigger_irs_investigation()
        
        # Execute sale
        result = await PortfolioManager.sell_crypto(user_id, ticker, amount)
        
        if result["success"]:
            details = result["details"]
            
            # If IRS investigation triggered, apply penalty AFTER successful sale
            if irs_investigation:
                penalty_percent = irs_investigation["penalty_percent"]
                
                # Get current user state after sale
                user = await get_user(user_id)
                current_points = user.get("points", 0)
                
                # Get portfolio to calculate crypto value
                from bot.crypto.models import CryptoModels
                portfolio = await CryptoModels.get_user_portfolio(user_id)
                total_crypto_value = 0
                
                holdings = portfolio.get("holdings", {})
                for hold_ticker, hold_amount in holdings.items():
                    coin = await CryptoModels.get_coin(hold_ticker)
                    if coin:
                        total_crypto_value += hold_amount * coin["current_price"]
                
                # Calculate penalties
                points_penalty = current_points * penalty_percent
                crypto_penalty_percent = penalty_percent
                
                # Apply points penalty
                await update_user_points(user_id, -points_penalty)
                
                # Apply crypto penalty by reducing all holdings
                for hold_ticker, hold_amount in holdings.items():
                    new_amount = hold_amount * (1 - crypto_penalty_percent)
                    amount_to_remove = hold_amount - new_amount
                    
                    if amount_to_remove > 0:
                        # Update portfolio to remove crypto
                        await CryptoModels.update_portfolio(
                            user_id=user_id,
                            ticker=hold_ticker,
                            amount=-amount_to_remove,
                            cost_change=0,
                            is_buy=False,
                            sale_value=0  # IRS seizure, no sale value
                        )
                
                # Send IRS investigation embed
                irs_embed = create_embed(
                    title="🚨 IRS INVESTIGATION!",
                    description=irs_investigation["message"],
                    color=0xff0000,
                    fields=[{
                        "name": "💸 Assets Seized",
                        "value": (
                            f"**Points Lost:** {format_money(points_penalty)}\n"
                            f"**Crypto Reduced:** {penalty_percent*100:.1f}% of all holdings\n"
                            f"**Total Value Lost:** ~{format_money(points_penalty + (total_crypto_value * penalty_percent))}"
                        ),
                        "inline": False
                    }]
                )
                await interaction.followup.send(embed=irs_embed)
                
                # Update new points in details
                updated_user = await get_user(user_id)
                details["new_points"] = updated_user.get("points", 0)
            
            embed = create_embed(
                title="✅ Sale Successful!",
                description=result["message"],
                color=0x00ff00,
                fields=[{
                    "name": "Transaction Details",
                    "value": (
                        f"**Coins Sold:** {details['coins_sold']} {ticker}\n"
                        f"**Price per Coin:** {format_money(details['price_per_coin'])}\n"
                        f"**Gross Value:** {format_money(details['gross_value'])}\n"
                        f"**Transaction Fee:** {format_money(details['fee'])} ({TRANSACTION_FEE*100}%)\n"
                        f"**Net Received:** {format_money(details['net_value'])}\n"
                        f"**New Balance:** {format_money(details['new_points'])}"
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
                    f"**Total Value:** {format_money(details['total_value'])}\n"
                    f"**Total Fee:** {format_money(details['total_fee'])}\n"
                    f"**Coins Sold:** {details['coins_sold']} different types\n"
                    f"**New Balance:** {format_money(details['new_points'])}"
                ),
                "inline": False
            }]
            
            # Add detailed breakdown if not too many coins
            if len(details['sold_holdings']) <= 8:
                breakdown_text = ""
                for holding in details['sold_holdings']:
                    breakdown_text += f"**{holding['ticker']}:** {format_crypto_amount(holding['amount'])} @ {format_money(holding['price'])} = {format_money(holding['value'])}\n"
                
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