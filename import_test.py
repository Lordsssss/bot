#!/usr/bin/env python3
"""
Test all critical imports for deployment
"""

def test_critical_imports():
    """Test the imports that were causing deployment failures"""
    print("🧪 Testing Critical Imports")
    print("=" * 40)
    
    try:
        print("1. Testing chart_generator import...")
        # This should work now
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Mock the external dependencies first
        from unittest.mock import MagicMock
        
        # Mock discord
        sys.modules['discord'] = MagicMock()
        sys.modules['discord.ui'] = MagicMock()
        
        # Mock matplotlib 
        sys.modules['matplotlib'] = MagicMock()
        sys.modules['matplotlib.pyplot'] = MagicMock()
        sys.modules['matplotlib.dates'] = MagicMock()
        
        # Mock motor and other DB dependencies
        sys.modules['motor'] = MagicMock()
        sys.modules['motor.motor_asyncio'] = MagicMock()
        sys.modules['bot.db.connection'] = MagicMock()
        sys.modules['bot.utils.discord_helpers'] = MagicMock()
        sys.modules['bot.db.user'] = MagicMock()
        
        # Now test the specific import that was failing
        from bot.crypto.chart_generator import generate_price_chart
        print("✅ generate_price_chart import successful")
        
        print("\n2. Testing models imports...")
        from bot.crypto.models import get_crypto_portfolio, get_crypto_prices, get_crypto_transactions, get_crypto_trigger_orders
        print("✅ All models imports successful")
        
        print("\n3. Testing dashboard imports...")
        from bot.crypto.dashboards import PortfolioDashboard, MarketDashboard, TradingDashboard
        print("✅ All dashboard imports successful")
        
        print("\n4. Testing crypto commands import...")
        from bot.commands.crypto import crypto_portfolio, crypto_market, crypto_trading
        print("✅ All crypto command imports successful")
        
        print("\n🎉 ALL CRITICAL IMPORTS SUCCESSFUL!")
        print("The deployment error should be resolved.")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_critical_imports()
    exit(0 if success else 1)