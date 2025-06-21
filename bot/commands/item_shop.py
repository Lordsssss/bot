"""
Item shop and inventory commands
"""
import discord
from discord import Interaction, app_commands
from bot.utils.discord_helpers import check_channel_permission, create_embed
from bot.items.models import ItemsManager
from bot.items.constants import ITEMS, ITEM_CATEGORIES
from bot.utils.crypto_helpers import format_money
from datetime import datetime, timezone


@app_commands.command(name="shop", description="Browse the item shop")
async def shop(interaction: Interaction):
    """Display the item shop with all available items"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        shop_data = await ItemsManager.get_shop_items(user_id)
        active_cooldowns = await ItemsManager.get_active_cooldowns(user_id)
        
        # Create a set of items on cooldown for quick lookup
        cooldown_items = {cd["item_id"]: cd["remaining_hours"] for cd in active_cooldowns}
        
        embed = create_embed(
            title="🛒 Item Shop",
            description="Purchase functional items to enhance your gameplay!",
            color=0x3498db
        )
        
        for category_id, category_data in shop_data.items():
            if not category_data["items"]:
                continue
                
            category_name = category_data["name"]
            items_text = ""
            
            for item in category_data["items"]:
                effect_desc = ""
                if item["effect_type"] == "trade_boost":
                    effect_desc = f" (next {item['duration']} trades)"
                elif item["effect_type"] == "passive_income":
                    effect_desc = f" ({item['effect_value']*100:.1f}% every {item['effect_interval']}h for {item['duration']}h)"
                elif "duration" in item:
                    effect_desc = f" ({item['duration']}h duration)"
                
                # Add dynamic pricing indicator
                price_display = format_money(item['price'])
                if item.get("is_dynamic", False):
                    price_display += " 📈"
                
                # Add cooldown indicator
                item_id = item["id"]
                if item_id in cooldown_items:
                    cooldown_hours = cooldown_items[item_id]
                    price_display += f" ⏰({cooldown_hours:.1f}h)"
                
                items_text += f"**{item['name']}** - {price_display}{effect_desc}\n"
                items_text += f"*{item['description']}*\n\n"
            
            embed.add_field(
                name=f"{category_name}",
                value=items_text,
                inline=False
            )
        
        embed.set_footer(text="Use /buy <item_name> to purchase items | 📈 = Dynamic price | ⏰ = On cooldown | All items have 24h cooldown")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error loading shop: {str(e)}", ephemeral=True)


@app_commands.command(name="buy", description="Purchase an item from the shop")
@app_commands.describe(item="Name of the item to purchase")
async def buy_item(interaction: Interaction, item: str):
    """Purchase an item from the shop"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        # Find item by name (case insensitive, flexible matching)
        item_id = None
        item_lower = item.lower().strip()
        
        for id, item_data in ITEMS.items():
            item_name = item_data["name"].lower()
            
            # Exact match with display name
            if item_name == item_lower:
                item_id = id
                break
            
            # Match without emoji (remove emojis and extra spaces)
            import re
            clean_name = re.sub(r'[^\w\s-]', '', item_name).strip()
            clean_name = re.sub(r'\s+', ' ', clean_name)  # Normalize spaces
            
            if clean_name == item_lower:
                item_id = id
                break
            
            # Partial match for convenience (if input is unique enough)
            if item_lower in clean_name and len(item_lower) >= 3:
                item_id = id
                break
            
            # Special aliases/abbreviations
            aliases = {
                'sbf': 'sam_bankman_fried',
                'sam': 'sam_bankman_fried',
                'goldman': 'goldman_intern',
                'intern': 'goldman_intern',
                'influencer': 'crypto_influencer',
                'immigrant': 'underpaid_immigrant',
                'charm': 'lucky_charm',
                'tax': 'tax_evasion_license',
                'insider': 'market_insider_tip'
            }
            
            if item_lower in aliases and aliases[item_lower] == id:
                item_id = id
                break
        
        if not item_id:
            await interaction.followup.send(f"❌ Item '{item}' not found. Use `/shop` to see available items.", ephemeral=True)
            return
        
        # Purchase the item
        result = await ItemsManager.purchase_item(user_id, item_id)
        
        if result["success"]:
            item_data = result["item"]
            actual_price = result.get("actual_price", item_data.get("price", 0))
            
            embed = create_embed(
                title="✅ Purchase Successful!",
                description=result["message"],
                color=0x00ff00,
                fields=[{
                    "name": "📦 Item Details",
                    "value": (
                        f"**Name:** {item_data['name']}\n"
                        f"**Description:** {item_data['description']}\n"
                        f"**Price Paid:** {format_money(actual_price)}\n"
                        f"**Remaining Balance:** {format_money(result['remaining_points'])}"
                    ),
                    "inline": False
                }]
            )
            embed.set_footer(text="Use /use <item_name> to activate this item")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error purchasing item: {str(e)}", ephemeral=True)


@app_commands.command(name="inventory", description="View your item inventory")
async def inventory(interaction: Interaction):
    """Display user's item inventory"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        inventory = await ItemsManager.get_user_inventory(user_id)
        active_effects = await ItemsManager.get_active_effects(user_id)
        active_cooldowns = await ItemsManager.get_active_cooldowns(user_id)
        
        items = inventory.get("items", {})
        
        embed = create_embed(
            title="🎒 Your Inventory",
            description=f"Total spent: {format_money(inventory.get('total_spent', 0))} | Purchases: {inventory.get('purchases', 0)}",
            color=0x9b59b6
        )
        
        if not items:
            embed.add_field(
                name="📦 Items",
                value="Your inventory is empty. Visit `/shop` to purchase items!",
                inline=False
            )
        else:
            items_text = ""
            for item_id, quantity in items.items():
                if quantity > 0:
                    item_data = ITEMS.get(item_id, {})
                    item_name = item_data.get("name", item_id)
                    items_text += f"**{item_name}** x{quantity}\n"
            
            if items_text:
                embed.add_field(
                    name="📦 Items",
                    value=items_text,
                    inline=False
                )
        
        # Show active effects
        if active_effects:
            effects_text = ""
            for effect in active_effects:
                item_data = ITEMS.get(effect["item_id"], {})
                item_name = item_data.get("name", effect["item_id"])
                
                # Calculate remaining time/uses
                if effect.get("expires_at"):
                    expires_at = effect["expires_at"]
                    now = datetime.now(timezone.utc)
                    
                    # Handle timezone-naive datetimes from old records
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    
                    remaining = expires_at - now
                    hours = remaining.total_seconds() / 3600
                    if hours > 0:
                        effects_text += f"**{item_name}** - {hours:.1f}h remaining\n"
                elif effect.get("uses_remaining"):
                    effects_text += f"**{item_name}** - {effect['uses_remaining']} uses left\n"
                else:
                    effects_text += f"**{item_name}** - Active\n"
            
            embed.add_field(
                name="✨ Active Effects",
                value=effects_text if effects_text else "No active effects",
                inline=False
            )
        
        # Show active cooldowns
        if active_cooldowns:
            cooldowns_text = ""
            for cooldown in active_cooldowns:
                cooldowns_text += f"**{cooldown['item_name']}** - {cooldown['remaining_hours']:.1f}h remaining\n"
            
            embed.add_field(
                name="⏰ Item Cooldowns",
                value=cooldowns_text,
                inline=False
            )
        
        embed.set_footer(text="Use /use <item_name> to activate items")
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error loading inventory: {str(e)}", ephemeral=True)


@app_commands.command(name="use", description="Use/activate an item from your inventory")
@app_commands.describe(item="Name of the item to use")
async def use_item(interaction: Interaction, item: str):
    """Use an item from inventory"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        # Find item by name (case insensitive, flexible matching)
        item_id = None
        item_lower = item.lower().strip()
        
        for id, item_data in ITEMS.items():
            item_name = item_data["name"].lower()
            
            # Exact match with display name
            if item_name == item_lower:
                item_id = id
                break
            
            # Match without emoji (remove emojis and extra spaces)
            import re
            clean_name = re.sub(r'[^\w\s-]', '', item_name).strip()
            clean_name = re.sub(r'\s+', ' ', clean_name)  # Normalize spaces
            
            if clean_name == item_lower:
                item_id = id
                break
            
            # Partial match for convenience (if input is unique enough)
            if item_lower in clean_name and len(item_lower) >= 3:
                item_id = id
                break
            
            # Special aliases/abbreviations
            aliases = {
                'sbf': 'sam_bankman_fried',
                'sam': 'sam_bankman_fried',
                'goldman': 'goldman_intern',
                'intern': 'goldman_intern',
                'influencer': 'crypto_influencer',
                'immigrant': 'underpaid_immigrant',
                'charm': 'lucky_charm',
                'tax': 'tax_evasion_license',
                'insider': 'market_insider_tip'
            }
            
            if item_lower in aliases and aliases[item_lower] == id:
                item_id = id
                break
        
        if not item_id:
            await interaction.followup.send(f"❌ Item '{item}' not found. Use `/inventory` to see your items.", ephemeral=True)
            return
        
        # Use the item
        result = await ItemsManager.use_item(user_id, item_id)
        
        if result["success"]:
            item_data = result["item"]
            effect = result["effect"]
            
            # Create effect description
            effect_desc = ""
            if effect.get("expires_at"):
                remaining = effect["expires_at"] - datetime.utcnow()
                hours = remaining.total_seconds() / 3600
                effect_desc = f"Duration: {hours:.1f} hours"
            elif effect.get("uses_remaining"):
                effect_desc = f"Uses: {effect['uses_remaining']} remaining"
            
            embed = create_embed(
                title="✨ Item Activated!",
                description=result["message"],
                color=0x00ff00,
                fields=[{
                    "name": "🎯 Effect Details",
                    "value": (
                        f"**Name:** {item_data['name']}\n"
                        f"**Description:** {item_data['description']}\n"
                        f"**{effect_desc}**" if effect_desc else "**Active**"
                    ),
                    "inline": False
                }]
            )
            
            # Add specific effect info
            if item_data["effect_type"] == "trade_boost":
                embed.add_field(
                    name="📈 Trading Boost",
                    value="Your next trades will have better outcomes and reduced IRS investigation chance!",
                    inline=False
                )
            elif item_data["effect_type"] == "passive_income":
                tier_names = {
                    1: "👷 Underpaid Immigrant",
                    2: "🤓 Coked Up Goldman Intern", 
                    3: "🎭 Crypto Influencer",
                    4: "👨‍💼 Sam Bankman-Fried"
                }
                tier = item_data.get("tier", 1)
                trader_name = tier_names.get(tier, "Auto-Trader")
                
                embed.add_field(
                    name=f"🤖 {trader_name}",
                    value=f"Earning {item_data['effect_value']*100:.1f}% of your balance every {item_data['effect_interval']} hours!",
                    inline=False
                )
            elif item_data["effect_type"] == "casino_boost":
                embed.add_field(
                    name="🍀 Lucky Charm",
                    value="Your casino games now have improved odds!",
                    inline=False
                )
            elif item_data["effect_type"] == "fee_immunity":
                embed.add_field(
                    name="🚫 Tax Evasion License",
                    value="No transaction fees and immunity from IRS investigations!",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ {result['message']}", ephemeral=True)
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error using item: {str(e)}", ephemeral=True)