"""
Translation system for multi-language support
"""

# English translations (default)
TRANSLATIONS = {
    "en": {
        # Common messages
        "balance_message": "{mention}, your balance is {balance}.",
        "insufficient_funds": "Insufficient funds! You have {current} but need {needed}.",
        "channel_not_allowed": "This channel is not configured for bot commands.",
        "admin_only": "This command requires administrator permissions.",
        "error_occurred": "An error occurred: {error}",
        
        # Crypto trading
        "purchase_successful": "✅ Purchase Successful!",
        "sale_successful": "✅ Sale Successful!",
        "sell_all_successful": "✅ Sell All Successful!",
        "crypto_not_found": "Crypto {ticker} not found!\nAvailable: {available}",
        "amount_must_be_positive": "Amount must be a positive number!",
        "amount_must_be_number_or_all": "Amount must be a number or 'all'!",
        "need_minimum_points": "You need at least 1 point to buy crypto!",
        "minimum_amount": "Minimum amount is {min_amount}!",
        "no_crypto_holdings": "No crypto holdings to sell!",
        "insufficient_crypto": "Insufficient {ticker}! You have {current} but want to sell {requested}.",
        
        # Transaction details
        "transaction_details": "Transaction Details",
        "coins_received": "Coins Received",
        "coins_sold": "Coins Sold", 
        "price_per_coin": "Price per Coin",
        "total_cost": "Total Cost",
        "gross_value": "Gross Value",
        "transaction_fee": "Transaction Fee",
        "net_received": "Net Received",
        "remaining_points": "Remaining Points",
        "new_balance": "New Balance",
        
        # IRS Investigation
        "irs_investigation_title": "🚨 IRS INVESTIGATION!",
        "irs_investigation_message": "🚨 **IRS INVESTIGATION TRIGGERED!** 🚨\n\nThe IRS has flagged your suspicious trading activity!\n**Asset Seizure:** {penalty}% of all assets!\nYour crypto holdings and points balance have been reduced.\n\n*Always report your crypto gains to the IRS!* 📋",
        "assets_seized": "💸 Assets Seized",
        "points_lost": "Points Lost",
        "crypto_reduced": "Crypto Reduced",
        "total_value_lost": "Total Value Lost",
        
        # Portfolio and market
        "crypto_market_prices": "🪙 Crypto Market Prices",
        "current_prices": "Current Prices",
        "prices_update_footer": "Prices update every ~15-30 seconds | Use /crypto charts <ticker> for detailed view",
        "no_crypto_data": "No crypto data available! Market might be initializing...",
        "portfolio_title": "📊 Your Crypto Portfolio",
        "no_holdings": "No crypto holdings yet!\nUse `/crypto buy` to start trading.",
        "current_holdings": "Current Holdings",
        "portfolio_summary": "Portfolio Summary",
        
        # Weekly reset
        "weekly_winners_title": "🎉 Weekly Winners 🎉",
        "points_champion": "🎲 Points Champion",
        "crypto_champion": "📈 Crypto Champion",
        "reset_footer": "All systems have been reset for a fresh start!",
        "weekly_reset_complete": "Weekly reset complete: points reset, crypto system wiped, winners recorded.",
        
        # Admin commands
        "language_updated": "Server language updated to {language_name}!",
        "channel_added": "Channel {channel} added to allowed channels!",
        "channel_removed": "Channel {channel} removed from allowed channels!",
        "channels_cleared": "All channel restrictions cleared. Bot can now be used in any channel!",
        "invalid_language": "Invalid language! Supported languages: {languages}",
        "config_title": "🔧 Server Configuration",
        "current_language": "Current Language",
        "allowed_channels": "Allowed Channels",
        "all_channels": "All channels allowed",
        "no_channels": "No channels configured",
    },
    
    # French translations
    "fr": {
        # Common messages
        "balance_message": "{mention}, votre solde est de {balance}.",
        "insufficient_funds": "Fonds insuffisants ! Vous avez {current} mais avez besoin de {needed}.",
        "channel_not_allowed": "Ce canal n'est pas configuré pour les commandes du bot.",
        "admin_only": "Cette commande nécessite des permissions d'administrateur.",
        "error_occurred": "Une erreur s'est produite : {error}",
        
        # Crypto trading
        "purchase_successful": "✅ Achat Réussi !",
        "sale_successful": "✅ Vente Réussie !",
        "sell_all_successful": "✅ Vente Totale Réussie !",
        "crypto_not_found": "Crypto {ticker} introuvable !\nDisponibles : {available}",
        "amount_must_be_positive": "Le montant doit être un nombre positif !",
        "amount_must_be_number_or_all": "Le montant doit être un nombre ou 'all' !",
        "need_minimum_points": "Vous avez besoin d'au moins 1 point pour acheter de la crypto !",
        "minimum_amount": "Le montant minimum est {min_amount} !",
        "no_crypto_holdings": "Aucune crypto en possession à vendre !",
        "insufficient_crypto": "{ticker} insuffisant ! Vous avez {current} mais voulez vendre {requested}.",
        
        # Transaction details
        "transaction_details": "Détails de la Transaction",
        "coins_received": "Coins Reçus",
        "coins_sold": "Coins Vendus",
        "price_per_coin": "Prix par Coin",
        "total_cost": "Coût Total",
        "gross_value": "Valeur Brute",
        "transaction_fee": "Frais de Transaction",
        "net_received": "Net Reçu",
        "remaining_points": "Points Restants",
        "new_balance": "Nouveau Solde",
        
        # IRS Investigation
        "irs_investigation_title": "🚨 ENQUÊTE IRS !",
        "irs_investigation_message": "🚨 **ENQUÊTE IRS DÉCLENCHÉE !** 🚨\n\nL'IRS a signalé votre activité de trading suspecte !\n**Saisie d'Actifs :** {penalty}% de tous les actifs !\nVos cryptos et votre solde de points ont été réduits.\n\n*Toujours déclarer vos gains crypto à l'IRS !* 📋",
        "assets_seized": "💸 Actifs Saisis",
        "points_lost": "Points Perdus",
        "crypto_reduced": "Crypto Réduit",
        "total_value_lost": "Valeur Totale Perdue",
        
        # Portfolio and market
        "crypto_market_prices": "🪙 Prix du Marché Crypto",
        "current_prices": "Prix Actuels",
        "prices_update_footer": "Prix mis à jour toutes les ~15-30 secondes | Utilisez /crypto charts <ticker> pour vue détaillée",
        "no_crypto_data": "Aucune donnée crypto disponible ! Le marché pourrait être en cours d'initialisation...",
        "portfolio_title": "📊 Votre Portefeuille Crypto",
        "no_holdings": "Aucune crypto en possession !\nUtilisez `/crypto buy` pour commencer à trader.",
        "current_holdings": "Possessions Actuelles",
        "portfolio_summary": "Résumé du Portefeuille",
        
        # Weekly reset
        "weekly_winners_title": "🎉 Gagnants Hebdomadaires 🎉",
        "points_champion": "🎲 Champion des Points",
        "crypto_champion": "📈 Champion Crypto",
        "reset_footer": "Tous les systèmes ont été remis à zéro pour un nouveau départ !",
        "weekly_reset_complete": "Remise à zéro hebdomadaire terminée : points remis à zéro, système crypto effacé, gagnants enregistrés.",
        
        # Admin commands
        "language_updated": "Langue du serveur mise à jour vers {language_name} !",
        "channel_added": "Canal {channel} ajouté aux canaux autorisés !",
        "channel_removed": "Canal {channel} retiré des canaux autorisés !",
        "channels_cleared": "Toutes les restrictions de canal supprimées. Le bot peut maintenant être utilisé dans n'importe quel canal !",
        "invalid_language": "Langue invalide ! Langues supportées : {languages}",
        "config_title": "🔧 Configuration du Serveur",
        "current_language": "Langue Actuelle",
        "allowed_channels": "Canaux Autorisés",
        "all_channels": "Tous les canaux autorisés",
        "no_channels": "Aucun canal configuré",
    }
}

def get_text(guild_id: str, key: str, language: str = None, **kwargs) -> str:
    """Get translated text for a given key and server"""
    if language is None:
        language = "en"  # Default fallback
    
    # Get the translation, fallback to English if not found
    text = TRANSLATIONS.get(language, {}).get(key) or TRANSLATIONS["en"].get(key, key)
    
    # Format with provided arguments
    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text

def get_supported_languages() -> list:
    """Get list of supported language codes"""
    return list(TRANSLATIONS.keys())

def is_language_supported(language: str) -> bool:
    """Check if a language is supported"""
    return language in TRANSLATIONS