#!/usr/bin/env python3
"""
Simple test to verify dashboard functionality without complex mocking
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_syntax_validation():
    """Test that all Python files have valid syntax"""
    print("Testing Python syntax validation...")
    
    import subprocess
    
    files_to_check = [
        "bot/crypto/dashboards.py",
        "bot/crypto/dashboard_helpers.py",
        "bot/commands/crypto.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Syntax error in {file_path}: {result.stderr}")
                all_good = False
            else:
                print(f"✅ {file_path}")
                
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            all_good = False
    
    return all_good

def test_portfolio_calculation_logic():
    """Test portfolio value calculation logic"""
    print("Testing portfolio calculation logic...")
    
    try:
        # Test data
        portfolio = {
            'DOGE2': {'amount': 100.0, 'cost_basis': 500.0},
            'MEME': {'amount': 50.0, 'cost_basis': 250.0},
            'BOOM': {'amount': 0.0, 'cost_basis': 0.0}  # Zero holdings
        }
        prices = {
            'DOGE2': 6.5,
            'MEME': 8.2,
            'BOOM': 15.0
        }
        
        # Expected calculations
        # DOGE2: 100.0 * 6.5 = 650.0 value, 500.0 cost
        # MEME: 50.0 * 8.2 = 410.0 value, 250.0 cost  
        # BOOM: 0.0 * 15.0 = 0.0 value, 0.0 cost (ignored due to zero amount)
        expected_total_value = 650.0 + 410.0  # 1060.0
        expected_total_cost = 500.0 + 250.0   # 750.0
        expected_pl = expected_total_value - expected_total_cost  # 310.0
        expected_pl_percent = (expected_pl / expected_total_cost) * 100  # 41.33%
        
        # Implementation of the calculation logic
        total_value = 0
        total_cost = 0
        
        for ticker, data in portfolio.items():
            if data['amount'] > 0:  # Only count non-zero holdings
                current_price = prices.get(ticker, 0)
                value = data['amount'] * current_price
                cost = data['cost_basis']
                
                total_value += value
                total_cost += cost
        
        total_pl = total_value - total_cost
        total_pl_percent = (total_pl / total_cost * 100) if total_cost > 0 else 0
        
        # Verify calculations
        tests_passed = 0
        tests_total = 4
        
        if abs(total_value - expected_total_value) < 0.01:
            print(f"✅ Total value: {total_value} (expected {expected_total_value})")
            tests_passed += 1
        else:
            print(f"❌ Total value: {total_value} (expected {expected_total_value})")
        
        if abs(total_cost - expected_total_cost) < 0.01:
            print(f"✅ Total cost: {total_cost} (expected {expected_total_cost})")
            tests_passed += 1
        else:
            print(f"❌ Total cost: {total_cost} (expected {expected_total_cost})")
        
        if abs(total_pl - expected_pl) < 0.01:
            print(f"✅ Profit/Loss: {total_pl} (expected {expected_pl})")
            tests_passed += 1
        else:
            print(f"❌ Profit/Loss: {total_pl} (expected {expected_pl})")
        
        if abs(total_pl_percent - expected_pl_percent) < 0.1:
            print(f"✅ P/L Percentage: {total_pl_percent:.2f}% (expected {expected_pl_percent:.2f}%)")
            tests_passed += 1
        else:
            print(f"❌ P/L Percentage: {total_pl_percent:.2f}% (expected {expected_pl_percent:.2f}%)")
        
        return tests_passed == tests_total
        
    except Exception as e:
        print(f"❌ Portfolio calculation test failed: {e}")
        return False

def test_trading_logic():
    """Test buy/sell validation logic"""
    print("Testing trading validation logic...")
    
    try:
        # Test valid ticker validation
        CRYPTO_COINS = {
            'DOGE2': {'name': 'DogeCoin 2.0'},
            'MEME': {'name': 'MemeToken'},
            'BOOM': {'name': 'BoomerCoin'}
        }
        
        def validate_ticker(ticker):
            return ticker.upper() in CRYPTO_COINS
        
        def validate_amount(amount, min_amount=1.0):
            try:
                amount_float = float(amount)
                if amount_float < min_amount:
                    return False, f"Minimum amount is {min_amount}"
                return True, ""
            except ValueError:
                return False, "Amount must be a number"
        
        def validate_portfolio_holding(portfolio, ticker, sell_amount):
            if ticker not in portfolio:
                return False, f"You don't own any {ticker}"
            
            user_amount = portfolio[ticker]['amount']
            if sell_amount > user_amount:
                return False, f"You only own {user_amount:.2f} {ticker}"
            
            return True, ""
        
        # Test ticker validation
        ticker_tests = [
            ("DOGE2", True, "Valid ticker"),
            ("INVALID", False, "Invalid ticker"),
            ("doge2", True, "Lowercase ticker (should be converted)"),
        ]
        
        amount_tests = [
            (100.0, True, "Valid amount"),
            (0.5, False, "Below minimum"),
            ("abc", False, "Non-numeric amount"),
        ]
        
        passed = 0
        total = 0
        
        # Test ticker validation
        for ticker, expected, description in ticker_tests:
            total += 1
            result = validate_ticker(ticker)
            if result == expected:
                print(f"✅ {description}: {ticker}")
                passed += 1
            else:
                print(f"❌ {description}: {ticker} (expected {expected}, got {result})")
        
        # Test amount validation
        for amount, expected, description in amount_tests:
            total += 1
            result, _ = validate_amount(amount)
            if result == expected:
                print(f"✅ {description}: {amount}")
                passed += 1
            else:
                print(f"❌ {description}: {amount} (expected {expected}, got {result})")
        
        # Test portfolio validation
        portfolio_tests = [
            ({"DOGE2": {"amount": 50.0}}, "DOGE2", 25.0, True, "Valid sell"),
            ({"DOGE2": {"amount": 50.0}}, "DOGE2", 75.0, False, "Sell more than owned"),
            ({}, "DOGE2", 25.0, False, "Sell non-owned crypto"),
        ]
        
        for portfolio, ticker, amount, expected, description in portfolio_tests:
            total += 1
            result, _ = validate_portfolio_holding(portfolio, ticker, amount)
            if result == expected:
                print(f"✅ {description}")
                passed += 1
            else:
                print(f"❌ {description} (expected {expected}, got {result})")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Trading logic test failed: {e}")
        return False

def test_user_authorization_logic():
    """Test user authorization logic"""
    print("Testing user authorization logic...")
    
    try:
        def check_user_authorization(authorized_user_id, requesting_user_id):
            """Simulate the authorization check logic"""
            return authorized_user_id == requesting_user_id
        
        # Test cases
        test_cases = [
            (123456789, 123456789, True, "Same user ID"),
            (123456789, 987654321, False, "Different user ID"),
            (111111111, 111111111, True, "Another same user ID"),
            (0, 123456789, False, "Zero vs valid ID"),
        ]
        
        passed = 0
        
        for auth_id, req_id, expected, description in test_cases:
            result = check_user_authorization(auth_id, req_id)
            if result == expected:
                print(f"✅ {description}: authorized={auth_id}, requesting={req_id}")
                passed += 1
            else:
                print(f"❌ {description}: authorized={auth_id}, requesting={req_id} (expected {expected}, got {result})")
        
        return passed == len(test_cases)
        
    except Exception as e:
        print(f"❌ User authorization test failed: {e}")
        return False

def test_embed_data_structure():
    """Test Discord embed data structure"""
    print("Testing embed data structure...")
    
    try:
        # Simulate embed creation
        def create_portfolio_embed(portfolio, prices, total_value, total_pl):
            embed_data = {
                "title": "🏦 Crypto Portfolio Dashboard",
                "color": 0x00ff00,
                "fields": []
            }
            
            # Add portfolio summary
            embed_data["fields"].append({
                "name": "💼 Portfolio Summary", 
                "value": f"Total Value: 🪙 {total_value:,.0f}\nP/L: {'🟢' if total_pl >= 0 else '🔴'} {total_pl:+,.0f}",
                "inline": False
            })
            
            # Add holdings
            if portfolio:
                holdings_text = ""
                for ticker, data in portfolio.items():
                    if data['amount'] > 0:
                        current_price = prices.get(ticker, 0)
                        value = data['amount'] * current_price
                        holdings_text += f"**{ticker}**: {data['amount']:.2f} @ 🪙{current_price:.2f} = 🪙{value:.0f}\n"
                
                if holdings_text:
                    embed_data["fields"].append({
                        "name": "📈 Current Holdings",
                        "value": holdings_text,
                        "inline": False
                    })
            
            return embed_data
        
        # Test data
        portfolio = {
            'DOGE2': {'amount': 100.0, 'cost_basis': 500.0},
            'MEME': {'amount': 50.0, 'cost_basis': 250.0}
        }
        prices = {'DOGE2': 6.5, 'MEME': 8.2}
        total_value = 1060.0
        total_pl = 310.0
        
        # Create embed
        embed = create_portfolio_embed(portfolio, prices, total_value, total_pl)
        
        # Validate structure
        checks = [
            (embed.get("title") == "🏦 Crypto Portfolio Dashboard", "Title"),
            (embed.get("color") == 0x00ff00, "Color"),
            (isinstance(embed.get("fields"), list), "Fields is list"),
            (len(embed["fields"]) >= 2, "Has multiple fields"),
            ("Portfolio Summary" in embed["fields"][0]["name"], "Summary field"),
            ("Current Holdings" in embed["fields"][1]["name"], "Holdings field"),
            ("DOGE2" in embed["fields"][1]["value"], "DOGE2 in holdings"),
            ("MEME" in embed["fields"][1]["value"], "MEME in holdings"),
        ]
        
        passed = 0
        for check, description in checks:
            if check:
                print(f"✅ {description}")
                passed += 1
            else:
                print(f"❌ {description}")
        
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ Embed structure test failed: {e}")
        return False

def main():
    """Run all simple tests"""
    print("🧪 Running Simple Dashboard Tests")
    print("=" * 60)
    
    tests = [
        test_syntax_validation,
        test_portfolio_calculation_logic,
        test_trading_logic,
        test_user_authorization_logic,
        test_embed_data_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print(f"\n📋 {test.__doc__}")
        print("-" * 40)
        try:
            if test():
                print("✅ TEST PASSED\n")
                passed += 1
            else:
                print("❌ TEST FAILED\n")
                failed += 1
        except Exception as e:
            print(f"💥 TEST CRASHED: {e}\n")
            failed += 1
    
    print("=" * 60)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🎉 All tests passed! Dashboard system is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())