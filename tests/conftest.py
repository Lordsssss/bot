"""
Test configuration and shared fixtures
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_interaction():
    """Mock Discord interaction object"""
    interaction = MagicMock()
    interaction.user.id = 123456789
    interaction.guild_id = 987654321
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.edit_original_response = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "user_id": "123456789",
        "points": 1000.0,
        "username": "test_user",
        "created_at": datetime.utcnow()
    }


@pytest.fixture
def mock_crypto_portfolio():
    """Mock crypto portfolio data"""
    return {
        "DOGE2": {
            "amount": 100.0,
            "cost_basis": 500.0
        },
        "MEME": {
            "amount": 50.0,
            "cost_basis": 250.0
        }
    }


@pytest.fixture
def mock_crypto_prices():
    """Mock crypto price data"""
    return {
        "DOGE2": 6.5,
        "MEME": 8.2,
        "BOOM": 15.7,
        "YOLO": 3.1,
        "HODL": 12.4,
        "REKT": 2.8,
        "PUMP": 9.9,
        "DUMP": 1.5,
        "MOON": 25.3,
        "CHAD": 18.6
    }


@pytest.fixture
def mock_transactions():
    """Mock transaction history"""
    return [
        {
            "user_id": "123456789",
            "ticker": "DOGE2",
            "action": "buy",
            "amount": 50.0,
            "price": 5.0,
            "timestamp": datetime.utcnow()
        },
        {
            "user_id": "123456789",
            "ticker": "MEME",
            "action": "sell",
            "amount": 25.0,
            "price": 8.0,
            "timestamp": datetime.utcnow()
        }
    ]


@pytest.fixture
def mock_trigger_orders():
    """Mock trigger orders"""
    return [
        {
            "user_id": "123456789",
            "ticker": "DOGE2",
            "amount": 100.0,
            "target_gain_percent": 25.0,
            "trigger_price": 6.25,
            "created_at": datetime.utcnow()
        }
    ]


@pytest.fixture
async def mock_db():
    """Mock database collections"""
    mock_collection = AsyncMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.find = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    return mock_collection


@pytest.fixture
def mock_portfolio_manager():
    """Mock PortfolioManager"""
    manager = MagicMock()
    manager.buy_crypto = AsyncMock(return_value={
        "success": True,
        "message": "Purchase successful",
        "details": {
            "coins_received": 100.0,
            "price_per_coin": 5.0,
            "total_cost": 500.0,
            "fee": 5.0,
            "remaining_points": 495.0
        }
    })
    manager.sell_crypto = AsyncMock(return_value={
        "success": True,
        "message": "Sale successful",
        "details": {
            "coins_sold": 50.0,
            "price_per_coin": 6.0,
            "gross_value": 300.0,
            "fee": 3.0,
            "net_value": 297.0,
            "new_points": 792.0
        }
    })
    return manager


@pytest.fixture
def mock_items_manager():
    """Mock ItemsManager for special effects"""
    manager = MagicMock()
    manager.check_effect_active = AsyncMock(return_value=False)
    return manager