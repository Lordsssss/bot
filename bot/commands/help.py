"""
Help command for the bot with multi-language support
"""
import discord
from discord import Interaction, app_commands
from bot.utils.discord_helpers import check_channel_permission, create_embed
from bot.db.server_config import get_server_language
from bot.utils.translations import get_text


@app_commands.command(name="help", description="Show all bot commands and features")
async def help_command(interaction: Interaction):
    """Display comprehensive help information"""
    if not await check_channel_permission(interaction):
        return
    
    try:
        await interaction.response.defer()
        
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        language = await get_server_language(guild_id)
        
        # Create main help embed
        if language == "fr":
            title = "🤖 Guide du Bot de Trading"
            description = "Bot de jeu complet avec système de points, casino et trading crypto !"
            
            # Basic Commands
            basic_commands = """
**💰 Commandes de Base**
`/balance` - Voir votre solde de points
`/leaderboard` - Classement des joueurs
`/hall-of-fame` - Hall of Fame des gagnants
`/my-wins` - Vos victoires récentes
`/next-reset` - Temps avant la remise à zéro
`/weekly-limit` - Voir votre limite hebdomadaire
"""
            
            # Casino Commands  
            casino_commands = """
**🎰 Commandes de Casino**
`/coinflip <montant>` - Pile ou face (50% de chance)
`/dice <montant>` - Jeu de dés (chances variables)
`/slot <montant>` - Machine à sous
`/roulette <montant> <couleur>` - Roulette (rouge/noir)
`/give <@utilisateur> <montant>` - Donner des points
"""
            
            # Crypto Commands
            crypto_commands = """
**📈 Trading Crypto**
`/crypto prices` - Prix actuels des cryptos
`/crypto charts <ticker>` - Graphiques de prix
`/crypto buy <ticker> <montant|all>` - Acheter des cryptos
`/crypto sell <ticker> <montant>` - Vendre des cryptos
`/crypto sellall` - Vendre toutes les cryptos
`/crypto portfolio` - Voir votre portefeuille
`/crypto leaderboard` - Classement crypto
`/crypto history` - Historique des transactions
`/crypto analysis` - Analyse de marché détaillée
"""
            
            # Admin Commands
            admin_commands = """
**🔧 Commandes Admin**
`/config` - Configuration du serveur
`/config-language <en|fr>` - Définir la langue
`/config-channel-add <canal>` - Ajouter un canal autorisé
`/config-channel-remove <canal>` - Retirer un canal
`/config-channel-clear` - Autoriser tous les canaux
`/forcereset` - Forcer la remise à zéro hebdomadaire
"""
            
            # Features
            features = """
**✨ Fonctionnalités Spéciales**
• 🚨 **Enquêtes IRS** - 0.5% de chance lors des trades (perte 40-90% des actifs)
• 💰 **Format Monétaire** - Affichage professionnel ($1,234.56)
• 🎯 **"All In"** - Utilisez tous vos points avec `all`
• 📊 **Système P/L** - Suivi des profits/pertes historiques
• 🔄 **Remise à Zéro Hebdomadaire** - Champions points + crypto
• 🌐 **Multi-Serveur** - Configuration par serveur
"""
            
            footer = "💡 Conseil: Commencez avec /balance puis /crypto prices pour découvrir le trading !"
            
        else:  # English
            title = "🤖 Trading Bot Guide"
            description = "Complete gaming bot with points system, casino games, and crypto trading!"
            
            # Basic Commands
            basic_commands = """
**💰 Basic Commands**
`/balance` - Check your points balance
`/leaderboard` - Player leaderboard
`/hall-of-fame` - Hall of Fame winners
`/my-wins` - Your recent wins
`/next-reset` - Time until next reset
`/weekly-limit` - View your weekly limit
"""
            
            # Casino Commands  
            casino_commands = """
**🎰 Casino Commands**
`/coinflip <amount>` - Coin flip (50% chance)
`/dice <amount>` - Dice game (variable odds)
`/slot <amount>` - Slot machine
`/roulette <amount> <color>` - Roulette (red/black)
`/give <@user> <amount>` - Give points to user
"""
            
            # Crypto Commands
            crypto_commands = """
**📈 Crypto Trading**
`/crypto prices` - Current crypto prices
`/crypto charts <ticker>` - Price charts
`/crypto buy <ticker> <amount|all>` - Buy cryptocurrency
`/crypto sell <ticker> <amount>` - Sell cryptocurrency
`/crypto sellall` - Sell all crypto holdings
`/crypto portfolio` - View your portfolio
`/crypto leaderboard` - Crypto leaderboard
`/crypto history` - Transaction history
`/crypto analysis` - Detailed market analysis
"""
            
            # Admin Commands
            admin_commands = """
**🔧 Admin Commands**
`/config` - View server configuration
`/config-language <en|fr>` - Set server language
`/config-channel-add <channel>` - Add allowed channel
`/config-channel-remove <channel>` - Remove channel
`/config-channel-clear` - Allow all channels
`/forcereset` - Force weekly reset
"""
            
            # Features
            features = """
**✨ Special Features**
• 🚨 **IRS Investigations** - 0.5% chance on trades (40-90% asset loss)
• 💰 **Money Formatting** - Professional display ($1,234.56)
• 🎯 **"All In"** - Use all points with `all`
• 📊 **P/L Tracking** - Historical profit/loss tracking
• 🔄 **Weekly Reset** - Points + crypto champions
• 🌐 **Multi-Server** - Per-server configuration
"""
            
            footer = "💡 Tip: Start with /balance then /crypto prices to explore trading!"
        
        # Create paginated embeds
        embeds = []
        
        # Main overview embed
        main_embed = create_embed(
            title=title,
            description=description,
            color=0x3498db,
            fields=[
                {
                    "name": basic_commands.split('\n')[0].strip('*'),
                    "value": '\n'.join(basic_commands.split('\n')[1:]).strip(),
                    "inline": False
                }
            ],
            footer=footer
        )
        embeds.append(main_embed)
        
        # Casino embed
        casino_embed = create_embed(
            title=f"{title} - Casino",
            description=casino_commands,
            color=0xe74c3c,
            footer=footer
        )
        embeds.append(casino_embed)
        
        # Crypto embed
        crypto_embed = create_embed(
            title=f"{title} - Crypto",
            description=crypto_commands,
            color=0xf39c12,
            footer=footer
        )
        embeds.append(crypto_embed)
        
        # Admin & Features embed
        admin_embed = create_embed(
            title=f"{title} - Admin & Features",
            description=admin_commands + "\n" + features,
            color=0x9b59b6,
            footer=footer
        )
        embeds.append(admin_embed)
        
        # Send first embed, then follow up with others
        await interaction.followup.send(embed=embeds[0])
        
        for embed in embeds[1:]:
            await interaction.followup.send(embed=embed)
            
    except Exception as e:
        guild_id = str(interaction.guild_id) if interaction.guild_id else "0"
        language = await get_server_language(guild_id)
        message = get_text(guild_id, "error_occurred", language, error=str(e))
        
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)