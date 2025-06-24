"""
Unit tests for crypto dashboard helper functions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.crypto.dashboard_helpers import (
    execute_buy_crypto, execute_sell_crypto, calculate_portfolio_value,
    get_portfolio_pl, format_leaderboard_embed
)


class TestExecuteBuyCrypto:
    """Test execute_buy_crypto function"""
    
    @pytest.mark.asyncio
    async def test_buy_crypto_success(self, mock_interaction, mock_portfolio_manager):
        """Test successful crypto purchase"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.PortfolioManager', mock_portfolio_manager):
            result = await execute_buy_crypto(ctx, "DOGE2", "500")
        
        assert result["success"] is True
        assert "Successfully bought" in result["message"]
        mock_portfolio_manager.buy_crypto.assert_called_once_with("123456789", "DOGE2", 500.0)
    
    @pytest.mark.asyncio
    async def test_buy_crypto_all_amount(self, mock_interaction, mock_user, mock_portfolio_manager):
        """Test buying with 'all' amount"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_user', return_value=mock_user), \
             patch('bot.crypto.dashboard_helpers.PortfolioManager', mock_portfolio_manager):
            result = await execute_buy_crypto(ctx, "DOGE2", "all")
        
        assert result["success"] is True
        mock_portfolio_manager.buy_crypto.assert_called_once_with("123456789", "DOGE2", 1000.0)
    
    @pytest.mark.asyncio
    async def test_buy_crypto_insufficient_funds(self, mock_interaction, mock_user):
        """Test buying with insufficient funds"""
        ctx = mock_interaction
        poor_user = {**mock_user, "points": 0.5}
        
        with patch('bot.crypto.dashboard_helpers.get_user', return_value=poor_user):
            result = await execute_buy_crypto(ctx, "DOGE2", "all")
        
        assert result["success"] is False
        assert "need at least 1 point" in result["message"]
    
    @pytest.mark.asyncio
    async def test_buy_crypto_invalid_ticker(self, mock_interaction):
        """Test buying invalid cryptocurrency"""
        ctx = mock_interaction
        
        result = await execute_buy_crypto(ctx, "INVALID", "100")
        
        assert result["success"] is False
        assert "Unknown cryptocurrency" in result["message"]
    
    @pytest.mark.asyncio
    async def test_buy_crypto_invalid_amount(self, mock_interaction):
        """Test buying with invalid amount"""
        ctx = mock_interaction
        
        result = await execute_buy_crypto(ctx, "DOGE2", "not_a_number")
        
        assert result["success"] is False
        assert "must be a number" in result["message"]
    
    @pytest.mark.asyncio
    async def test_buy_crypto_minimum_amount(self, mock_interaction):
        """Test buying below minimum amount"""
        ctx = mock_interaction
        
        result = await execute_buy_crypto(ctx, "DOGE2", "0.5")
        
        assert result["success"] is False
        assert "Minimum purchase amount" in result["message"]
    
    @pytest.mark.asyncio
    async def test_buy_crypto_portfolio_manager_error(self, mock_interaction, mock_portfolio_manager):
        """Test handling PortfolioManager errors"""
        ctx = mock_interaction
        mock_portfolio_manager.buy_crypto.return_value = {
            "success": False,
            "message": "Insufficient points"
        }
        
        with patch('bot.crypto.dashboard_helpers.PortfolioManager', mock_portfolio_manager):
            result = await execute_buy_crypto(ctx, "DOGE2", "1000")
        
        assert result["success"] is False
        assert "Insufficient points" in result["message"]


class TestExecuteSellCrypto:
    """Test execute_sell_crypto function"""
    
    @pytest.mark.asyncio
    async def test_sell_crypto_success(self, mock_interaction, mock_crypto_portfolio, mock_portfolio_manager):
        """Test successful crypto sale"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value=mock_crypto_portfolio), \
             patch('bot.crypto.dashboard_helpers.PortfolioManager', mock_portfolio_manager):
            result = await execute_sell_crypto(ctx, "DOGE2", "50")
        
        assert result["success"] is True
        assert "Successfully sold" in result["message"]
        mock_portfolio_manager.sell_crypto.assert_called_once_with("123456789", "DOGE2", 50.0)
    
    @pytest.mark.asyncio
    async def test_sell_crypto_all_amount(self, mock_interaction, mock_crypto_portfolio, mock_portfolio_manager):
        """Test selling with 'all' amount"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value=mock_crypto_portfolio), \
             patch('bot.crypto.dashboard_helpers.PortfolioManager', mock_portfolio_manager):
            result = await execute_sell_crypto(ctx, "DOGE2", "all")
        
        assert result["success"] is True
        mock_portfolio_manager.sell_crypto.assert_called_once_with("123456789", "DOGE2", 100.0)
    
    @pytest.mark.asyncio
    async def test_sell_crypto_no_holdings(self, mock_interaction):
        """Test selling crypto not owned"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value={}):
            result = await execute_sell_crypto(ctx, "DOGE2", "50")
        
        assert result["success"] is False
        assert "don't own any" in result["message"]
    
    @pytest.mark.asyncio
    async def test_sell_crypto_insufficient_amount(self, mock_interaction, mock_crypto_portfolio):
        """Test selling more than owned"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value=mock_crypto_portfolio):
            result = await execute_sell_crypto(ctx, "DOGE2", "150")
        
        assert result["success"] is False
        assert "You only own" in result["message"]
    
    @pytest.mark.asyncio
    async def test_sell_crypto_invalid_amount(self, mock_interaction, mock_crypto_portfolio):
        """Test selling with invalid amount"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value=mock_crypto_portfolio):
            result = await execute_sell_crypto(ctx, "DOGE2", "not_a_number")
        
        assert result["success"] is False
        assert "must be a number" in result["message"]
    
    @pytest.mark.asyncio
    async def test_sell_crypto_zero_amount(self, mock_interaction, mock_crypto_portfolio):
        """Test selling zero amount"""
        ctx = mock_interaction
        
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value=mock_crypto_portfolio):
            result = await execute_sell_crypto(ctx, "DOGE2", "0")
        
        assert result["success"] is False
        assert "must be greater than 0" in result["message"]


class TestCalculatePortfolioValue:
    """Test calculate_portfolio_value function"""
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_success(self, mock_crypto_portfolio, mock_crypto_prices):
        """Test successful portfolio value calculation"""
        total_value, total_cost, total_pl, total_pl_percent = await calculate_portfolio_value(
            mock_crypto_portfolio, mock_crypto_prices
        )
        
        # DOGE2: 100.0 * 6.5 = 650.0, cost = 500.0
        # MEME: 50.0 * 8.2 = 410.0, cost = 250.0
        assert total_value == 1060.0
        assert total_cost == 750.0
        assert total_pl == 310.0
        assert abs(total_pl_percent - 41.33) < 0.1  # Allow small floating point error
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_empty_portfolio(self):
        """Test calculation with empty portfolio"""
        total_value, total_cost, total_pl, total_pl_percent = await calculate_portfolio_value({}, {})
        
        assert total_value == 0
        assert total_cost == 0
        assert total_pl == 0
        assert total_pl_percent == 0
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value_missing_prices(self, mock_crypto_portfolio):
        """Test calculation with missing price data"""
        partial_prices = {"DOGE2": 6.5}  # Missing MEME price
        
        total_value, total_cost, total_pl, total_pl_percent = await calculate_portfolio_value(
            mock_crypto_portfolio, partial_prices
        )
        
        # Only DOGE2 counted: 100.0 * 6.5 = 650.0, cost = 500.0
        # MEME ignored due to missing price
        assert total_value == 650.0
        assert total_cost == 750.0  # Both costs still counted
        assert total_pl == -100.0


class TestGetPortfolioPL:
    """Test get_portfolio_pl function"""
    
    @pytest.mark.asyncio
    async def test_get_portfolio_pl_success(self, mock_crypto_portfolio, mock_crypto_prices):
        """Test successful P/L calculation"""
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value=mock_crypto_portfolio), \
             patch('bot.crypto.dashboard_helpers.get_crypto_prices', return_value=mock_crypto_prices):
            result = await get_portfolio_pl("123456789")
        
        assert "all_time_pl" in result
        assert "current_pl" in result
        assert result["current_pl"] == 310.0  # Same as calculate_portfolio_value test
    
    @pytest.mark.asyncio
    async def test_get_portfolio_pl_empty_portfolio(self):
        """Test P/L calculation with empty portfolio"""
        with patch('bot.crypto.dashboard_helpers.get_crypto_portfolio', return_value={}), \
             patch('bot.crypto.dashboard_helpers.get_crypto_prices', return_value={}):
            result = await get_portfolio_pl("123456789")
        
        assert result["all_time_pl"] == 0
        assert result["current_pl"] == 0


class TestFormatLeaderboardEmbed:
    """Test format_leaderboard_embed function"""
    
    def test_format_leaderboard_embed(self):
        """Test leaderboard embed formatting"""
        embed = format_leaderboard_embed()
        
        assert embed.title == "🏆 Crypto Trading Leaderboard"
        assert embed.color == 0xffd700
        assert "Top crypto traders" in embed.description
        assert len(embed.fields) > 0
        assert "Coming Soon" in embed.fields[0].name