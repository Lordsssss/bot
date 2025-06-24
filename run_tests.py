#!/usr/bin/env python3
"""
Test runner script for the crypto dashboard system
"""
import sys
import subprocess
import os


def run_tests():
    """Run all tests with proper error handling"""
    print("🧪 Running Crypto Dashboard Tests")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest found")
    except ImportError:
        print("❌ pytest not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"])
            print("✅ Test dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install test dependencies: {e}")
            return 1
    
    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))
    
    # Run tests
    test_commands = [
        [sys.executable, "-m", "pytest", "tests/test_crypto/test_dashboard_helpers.py", "-v"],
        [sys.executable, "-m", "pytest", "tests/test_crypto/test_dashboards.py", "-v"],
        [sys.executable, "-m", "pytest", "tests/test_commands/test_crypto_commands.py", "-v"],
    ]
    
    total_passed = 0
    total_failed = 0
    
    for cmd in test_commands:
        print(f"\n🏃 Running: {' '.join(cmd)}")
        print("-" * 30)
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PASSED")
                # Count passed tests from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if "passed" in line and "failed" not in line:
                        try:
                            passed = int(line.split()[0])
                            total_passed += passed
                        except (ValueError, IndexError):
                            pass
            else:
                print("❌ FAILED")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                # Count failed tests
                lines = result.stderr.split('\n') + result.stdout.split('\n')
                for line in lines:
                    if "failed" in line:
                        try:
                            failed = int(line.split()[0])
                            total_failed += failed
                        except (ValueError, IndexError):
                            pass
                        
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            total_failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


def run_syntax_check():
    """Check syntax of Python files"""
    print("\n🔍 Running Syntax Checks")
    print("=" * 50)
    
    files_to_check = [
        "bot/crypto/dashboards.py",
        "bot/crypto/dashboard_helpers.py",
        "bot/commands/crypto.py",
        "tests/test_crypto/test_dashboard_helpers.py",
        "tests/test_crypto/test_dashboards.py",
        "tests/test_commands/test_crypto_commands.py",
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        print(f"Checking {file_path}...", end=" ")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅")
            else:
                print("❌")
                print(f"  Error: {result.stderr}")
                all_good = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_good = False
    
    if all_good:
        print("🎉 All syntax checks passed!")
    else:
        print("💥 Some syntax errors found!")
    
    return 0 if all_good else 1


if __name__ == "__main__":
    print("🚀 Crypto Dashboard Test Suite")
    print("=" * 50)
    
    # First run syntax checks
    syntax_result = run_syntax_check()
    
    if syntax_result != 0:
        print("❌ Syntax checks failed. Fix syntax errors before running tests.")
        sys.exit(1)
    
    # Then run actual tests
    test_result = run_tests()
    
    sys.exit(test_result)