"""
Integration tests for crypto dashboard views
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from bot.crypto.dashboards import (
    BaseCryptoDashboard, PortfolioDashboard, MarketDashboard, TradingDashboard
)


class TestBaseCryptoDashboard:
    """Test base dashboard functionality"""
    
    def test_init(self):
        """Test dashboard initialization"""
        dashboard = BaseCryptoDashboard(authorized_user_id=123456789)
        
        assert dashboard.authorized_user_id == 123456789
        assert dashboard.timeout == 300
    
    def test_init_custom_timeout(self):
        """Test dashboard initialization with custom timeout"""
        dashboard = BaseCryptoDashboard(authorized_user_id=123456789, timeout=600)
        
        assert dashboard.timeout == 600
    
    @pytest.mark.asyncio
    async def test_interaction_check_authorized_user(self, mock_interaction):
        """Test interaction check for authorized user"""
        dashboard = BaseCryptoDashboard(authorized_user_id=123456789)
        
        result = await dashboard.interaction_check(mock_interaction)
        
        assert result is True
        mock_interaction.response.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_interaction_check_unauthorized_user(self, mock_interaction):
        """Test interaction check for unauthorized user"""
        dashboard = BaseCryptoDashboard(authorized_user_id=999999999)
        mock_interaction.user.id = 123456789  # Different user
        
        result = await dashboard.interaction_check(mock_interaction)
        
        assert result is False
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "Only the user who opened this dashboard" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_on_timeout(self):
        """Test timeout behavior"""
        dashboard = BaseCryptoDashboard(authorized_user_id=123456789)
        
        # Add mock items to simulate UI components
        mock_button = MagicMock()
        mock_select = MagicMock()
        dashboard.children = [mock_button, mock_select]
        
        await dashboard.on_timeout()
        
        assert mock_button.disabled is True
        assert mock_select.disabled is True


class TestPortfolioDashboard:
    """Test portfolio dashboard functionality"""
    
    def test_init(self, mock_interaction):
        """Test portfolio dashboard initialization"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        assert dashboard.authorized_user_id == 123456789
        assert dashboard.ctx == mock_interaction
        assert dashboard.selected_coin is None
    
    @pytest.mark.asyncio
    async def test_get_portfolio_embed_empty_portfolio(self, mock_interaction):
        """Test portfolio embed generation with empty portfolio"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        with patch('bot.crypto.dashboards.get_crypto_portfolio', return_value=None), \
             patch('bot.crypto.dashboards.get_crypto_prices', return_value={}):
            embed = await dashboard._get_portfolio_embed()
        
        assert embed.title == "🏦 Crypto Portfolio Dashboard"
        assert embed.color == 0x00ff00
        assert "Your portfolio is empty" in embed.description
    
    @pytest.mark.asyncio
    async def test_get_portfolio_embed_with_holdings(self, mock_interaction, mock_crypto_portfolio, mock_crypto_prices):
        """Test portfolio embed generation with holdings"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        with patch('bot.crypto.dashboards.get_crypto_portfolio', return_value=mock_crypto_portfolio), \
             patch('bot.crypto.dashboards.get_crypto_prices', return_value=mock_crypto_prices), \
             patch('bot.crypto.dashboards.calculate_portfolio_value', return_value=(1060.0, 750.0, 310.0, 41.33)), \
             patch('bot.crypto.dashboards.get_crypto_transactions', return_value=[]):
            embed = await dashboard._get_portfolio_embed()
        
        assert embed.title == "🏦 Crypto Portfolio Dashboard"
        assert any("Portfolio Summary" in field.name for field in embed.fields)
        assert any("Current Holdings" in field.name for field in embed.fields)
    
    @pytest.mark.asyncio
    async def test_select_coin(self, mock_interaction):
        """Test coin selection"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        # Mock the select component
        mock_select = MagicMock()
        mock_select.values = ["DOGE2"]
        
        await dashboard.select_coin(mock_interaction, mock_select)
        
        assert dashboard.selected_coin == "DOGE2"
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "Selected **DogeCoin 2.0 (DOGE2)**" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_buy_all_no_coin_selected(self, mock_interaction):
        """Test buy all with no coin selected"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        # Mock button interaction
        mock_button = MagicMock()
        
        await dashboard.buy_all(mock_interaction, mock_button)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "Please select a cryptocurrency first" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_buy_all_success(self, mock_interaction):
        """Test successful buy all operation"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        dashboard.selected_coin = "DOGE2"
        
        mock_button = MagicMock()
        mock_result = {"success": True, "message": "Purchase successful"}
        
        with patch('bot.crypto.dashboards.execute_buy_crypto', return_value=mock_result), \
             patch.object(dashboard, '_get_portfolio_embed', return_value=MagicMock()):
            await dashboard.buy_all(mock_interaction, mock_button)
        
        mock_interaction.response.defer.assert_called_once()
        mock_interaction.edit_original_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_buy_all_failure(self, mock_interaction):
        """Test failed buy all operation"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        dashboard.selected_coin = "DOGE2"
        
        mock_button = MagicMock()
        mock_result = {"success": False, "message": "Insufficient funds"}
        
        with patch('bot.crypto.dashboards.execute_buy_crypto', return_value=mock_result):
            await dashboard.buy_all(mock_interaction, mock_button)
        
        mock_interaction.response.defer.assert_called_once()
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "❌ Insufficient funds" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_sell_all_success(self, mock_interaction):
        """Test successful sell all operation"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        dashboard.selected_coin = "DOGE2"
        
        mock_button = MagicMock()
        mock_result = {"success": True, "message": "Sale successful"}
        
        with patch('bot.crypto.dashboards.execute_sell_crypto', return_value=mock_result), \
             patch.object(dashboard, '_get_portfolio_embed', return_value=MagicMock()):
            await dashboard.sell_all(mock_interaction, mock_button)
        
        mock_interaction.response.defer.assert_called_once()
        mock_interaction.edit_original_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_portfolio(self, mock_interaction):
        """Test portfolio refresh"""
        dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_button = MagicMock()
        mock_embed = MagicMock()
        
        with patch.object(dashboard, '_get_portfolio_embed', return_value=mock_embed):
            await dashboard.refresh_portfolio(mock_interaction, mock_button)
        
        mock_interaction.response.edit_message.assert_called_once_with(embed=mock_embed, view=dashboard)


class TestMarketDashboard:
    """Test market dashboard functionality"""
    
    def test_init(self, mock_interaction):
        """Test market dashboard initialization"""
        dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        assert dashboard.authorized_user_id == 123456789
        assert dashboard.ctx == mock_interaction
        assert dashboard.selected_chart_coin == "all"
    
    @pytest.mark.asyncio
    async def test_get_market_embed_success(self, mock_interaction, mock_crypto_prices):
        """Test market embed generation"""
        dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        with patch('bot.crypto.dashboards.get_crypto_prices', return_value=mock_crypto_prices):
            embed = await dashboard._get_market_embed()
        
        assert embed.title == "📊 Crypto Market Dashboard"
        assert embed.color == 0x0099ff
        assert any("Current Prices" in field.name for field in embed.fields)
        assert any("Charts" in field.name for field in embed.fields)
    
    @pytest.mark.asyncio
    async def test_get_market_embed_no_prices(self, mock_interaction):
        """Test market embed with no price data"""
        dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        with patch('bot.crypto.dashboards.get_crypto_prices', return_value={}):
            embed = await dashboard._get_market_embed()
        
        assert "No price data available" in embed.description
    
    @pytest.mark.asyncio
    async def test_select_chart_coin_success(self, mock_interaction):
        """Test chart coin selection with successful chart generation"""
        dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_select = MagicMock()
        mock_select.values = ["DOGE2"]
        mock_chart_file = MagicMock()
        
        with patch('bot.crypto.dashboards.generate_price_chart', return_value=mock_chart_file):
            await dashboard.select_chart_coin(mock_interaction, mock_select)
        
        assert dashboard.selected_chart_coin == "DOGE2"
        mock_interaction.response.defer.assert_called_once()
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert call_args[1]["file"] == mock_chart_file
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_select_chart_coin_failure(self, mock_interaction):
        """Test chart coin selection with failed chart generation"""
        dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_select = MagicMock()
        mock_select.values = ["DOGE2"]
        
        with patch('bot.crypto.dashboards.generate_price_chart', return_value=None):
            await dashboard.select_chart_coin(mock_interaction, mock_select)
        
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "Failed to generate chart" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_show_leaderboard(self, mock_interaction):
        """Test leaderboard display"""
        dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_button = MagicMock()
        mock_embed = MagicMock()
        
        with patch('bot.crypto.dashboards.format_leaderboard_embed', return_value=mock_embed):
            await dashboard.show_leaderboard(mock_interaction, mock_button)
        
        mock_interaction.response.send_message.assert_called_once_with(embed=mock_embed, ephemeral=True)


class TestTradingDashboard:
    """Test trading dashboard functionality"""
    
    def test_init(self, mock_interaction):
        """Test trading dashboard initialization"""
        dashboard = TradingDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        assert dashboard.authorized_user_id == 123456789
        assert dashboard.ctx == mock_interaction
    
    @pytest.mark.asyncio
    async def test_get_trading_embed_no_orders(self, mock_interaction):
        """Test trading embed with no trigger orders"""
        dashboard = TradingDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        with patch('bot.crypto.dashboards.get_crypto_trigger_orders', return_value=[]):
            embed = await dashboard._get_trading_embed()
        
        assert embed.title == "⚡ Advanced Trading Dashboard"
        assert embed.color == 0xff6600
        assert any("Active Trigger Orders" in field.name for field in embed.fields)
        assert any("No active trigger orders" in field.value for field in embed.fields)
    
    @pytest.mark.asyncio
    async def test_get_trading_embed_with_orders(self, mock_interaction, mock_trigger_orders):
        """Test trading embed with trigger orders"""
        dashboard = TradingDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        with patch('bot.crypto.dashboards.get_crypto_trigger_orders', return_value=mock_trigger_orders):
            embed = await dashboard._get_trading_embed()
        
        assert embed.title == "⚡ Advanced Trading Dashboard"
        assert any("Active Trigger Orders" in field.name for field in embed.fields)
        orders_field = next(field for field in embed.fields if "Active Trigger Orders" in field.name)
        assert "DOGE2" in orders_field.value
        assert "25.0%" in orders_field.value
    
    @pytest.mark.asyncio
    async def test_show_history_no_transactions(self, mock_interaction):
        """Test transaction history with no transactions"""
        dashboard = TradingDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_button = MagicMock()
        
        with patch('bot.crypto.dashboards.get_crypto_transactions', return_value=[]):
            await dashboard.show_history(mock_interaction, mock_button)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        embed = call_args[1]["embed"]
        assert embed.title == "📝 Transaction History"
        assert embed.description == "No transactions found"
        assert call_args[1]["ephemeral"] is True
    
    @pytest.mark.asyncio
    async def test_show_history_with_transactions(self, mock_interaction, mock_transactions):
        """Test transaction history with transactions"""
        dashboard = TradingDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_button = MagicMock()
        
        with patch('bot.crypto.dashboards.get_crypto_transactions', return_value=mock_transactions):
            await dashboard.show_history(mock_interaction, mock_button)
        
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        embed = call_args[1]["embed"]
        assert embed.title == "📝 Transaction History"
        assert "BUY" in embed.description
        assert "SELL" in embed.description
        assert "DOGE2" in embed.description
        assert "MEME" in embed.description


class TestDashboardNavigation:
    """Test navigation between dashboards"""
    
    @pytest.mark.asyncio
    async def test_portfolio_to_market_navigation(self, mock_interaction):
        """Test navigation from portfolio to market dashboard"""
        portfolio_dashboard = PortfolioDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_button = MagicMock()
        mock_embed = MagicMock()
        
        with patch('bot.crypto.dashboards.MarketDashboard') as MockMarketDashboard:
            mock_market_instance = MockMarketDashboard.return_value
            mock_market_instance._get_market_embed = AsyncMock(return_value=mock_embed)
            
            await portfolio_dashboard.market_dashboard(mock_interaction, mock_button)
        
        MockMarketDashboard.assert_called_once_with(123456789, mock_interaction)
        mock_interaction.response.edit_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_market_to_trading_navigation(self, mock_interaction):
        """Test navigation from market to trading dashboard"""
        market_dashboard = MarketDashboard(authorized_user_id=123456789, ctx=mock_interaction)
        
        mock_button = MagicMock()
        mock_embed = MagicMock()
        
        with patch('bot.crypto.dashboards.TradingDashboard') as MockTradingDashboard:
            mock_trading_instance = MockTradingDashboard.return_value
            mock_trading_instance._get_trading_embed = AsyncMock(return_value=mock_embed)
            
            await market_dashboard.trading_dashboard(mock_interaction, mock_button)
        
        MockTradingDashboard.assert_called_once_with(123456789, mock_interaction)
        mock_interaction.response.edit_message.assert_called_once()