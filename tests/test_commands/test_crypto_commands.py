"""
Tests for crypto command functions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.commands.crypto import crypto_portfolio, crypto_market, crypto_trading


class TestCryptoCommands:
    """Test crypto command functions"""
    
    @pytest.mark.asyncio
    async def test_crypto_portfolio_command(self, mock_interaction):
        """Test crypto portfolio command"""
        mock_embed = MagicMock()
        mock_view = MagicMock()
        mock_view._get_portfolio_embed = AsyncMock(return_value=mock_embed)
        
        with patch('bot.commands.crypto.PortfolioDashboard', return_value=mock_view):
            await crypto_portfolio(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once_with(
            embed=mock_embed, 
            view=mock_view
        )
    
    @pytest.mark.asyncio
    async def test_crypto_market_command(self, mock_interaction):
        """Test crypto market command"""
        mock_embed = MagicMock()
        mock_view = MagicMock()
        mock_view._get_market_embed = AsyncMock(return_value=mock_embed)
        
        with patch('bot.commands.crypto.MarketDashboard', return_value=mock_view):
            await crypto_market(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once_with(
            embed=mock_embed, 
            view=mock_view
        )
    
    @pytest.mark.asyncio
    async def test_crypto_trading_command(self, mock_interaction):
        """Test crypto trading command"""
        mock_embed = MagicMock()
        mock_view = MagicMock()
        mock_view._get_trading_embed = AsyncMock(return_value=mock_embed)
        
        with patch('bot.commands.crypto.TradingDashboard', return_value=mock_view):
            await crypto_trading(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once_with(
            embed=mock_embed, 
            view=mock_view
        )
    
    @pytest.mark.asyncio
    async def test_crypto_portfolio_user_id_passed(self, mock_interaction):
        """Test that user ID is correctly passed to portfolio dashboard"""
        mock_view = MagicMock()
        mock_view._get_portfolio_embed = AsyncMock(return_value=MagicMock())
        
        with patch('bot.commands.crypto.PortfolioDashboard', return_value=mock_view) as MockDashboard:
            await crypto_portfolio(mock_interaction)
        
        MockDashboard.assert_called_once_with(mock_interaction.user.id, mock_interaction)
    
    @pytest.mark.asyncio
    async def test_crypto_market_user_id_passed(self, mock_interaction):
        """Test that user ID is correctly passed to market dashboard"""
        mock_view = MagicMock()
        mock_view._get_market_embed = AsyncMock(return_value=MagicMock())
        
        with patch('bot.commands.crypto.MarketDashboard', return_value=mock_view) as MockDashboard:
            await crypto_market(mock_interaction)
        
        MockDashboard.assert_called_once_with(mock_interaction.user.id, mock_interaction)
    
    @pytest.mark.asyncio
    async def test_crypto_trading_user_id_passed(self, mock_interaction):
        """Test that user ID is correctly passed to trading dashboard"""
        mock_view = MagicMock()
        mock_view._get_trading_embed = AsyncMock(return_value=MagicMock())
        
        with patch('bot.commands.crypto.TradingDashboard', return_value=mock_view) as MockDashboard:
            await crypto_trading(mock_interaction)
        
        MockDashboard.assert_called_once_with(mock_interaction.user.id, mock_interaction)