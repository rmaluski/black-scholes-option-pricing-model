#!/usr/bin/env python3
"""
Test script for option analysis functionality
"""

import sys
import os
from models import init_db
from option_data_fetcher import OptionDataFetcher

def test_option_analysis():
    """Test the option analysis functionality"""
    
    print("🧪 Testing Option Analysis Functionality")
    print("=" * 50)
    
    # Initialize database
    print("1. Initializing database...")
    try:
        init_db()
        print("   ✅ Database initialized successfully")
    except Exception as e:
        print(f"   ❌ Database initialization failed: {e}")
        return False
    
    # Create fetcher
    print("2. Creating OptionDataFetcher...")
    try:
        fetcher = OptionDataFetcher(risk_free_rate=0.05)
        print("   ✅ OptionDataFetcher created successfully")
    except Exception as e:
        print(f"   ❌ OptionDataFetcher creation failed: {e}")
        return False
    
    # Test stock data fetching
    print("3. Testing stock data fetching...")
    try:
        stock_data = fetcher.fetch_stock_data("AAPL")
        if stock_data and stock_data['current_price'] > 0:
            print(f"   ✅ AAPL stock data fetched: ${stock_data['current_price']:.2f}")
        else:
            print("   ❌ Failed to fetch valid AAPL stock data")
            return False
    except Exception as e:
        print(f"   ❌ Stock data fetching failed: {e}")
        return False
    
    # Test options data fetching
    print("4. Testing options data fetching...")
    try:
        calls_data, puts_data = fetcher.fetch_options_data("AAPL")
        total_options = len(calls_data) + len(puts_data)
        print(f"   ✅ AAPL options data fetched: {len(calls_data)} calls, {len(puts_data)} puts")
        
        if total_options == 0:
            print("   ⚠️ No options data found (this might be normal outside market hours)")
    except Exception as e:
        print(f"   ❌ Options data fetching failed: {e}")
        return False
    
    # Test Black-Scholes calculation
    print("5. Testing Black-Scholes calculation...")
    try:
        if calls_data:
            test_option = calls_data[0]
            strike = test_option.get('strike', 100)
            implied_vol = test_option.get('impliedVolatility', 0.3)
            
            bs_price = fetcher.calculate_black_scholes_for_option(
                test_option, stock_data['current_price'], 0.1, 'call'
            )
            
            if bs_price > 0:
                print(f"   ✅ Black-Scholes calculation successful: ${bs_price:.4f}")
            else:
                print("   ❌ Black-Scholes calculation returned zero or negative value")
                return False
        else:
            print("   ⚠️ Skipping Black-Scholes test (no options data available)")
    except Exception as e:
        print(f"   ❌ Black-Scholes calculation failed: {e}")
        return False
    
    # Test variance calculation
    print("6. Testing variance calculation...")
    try:
        current_price = 10.0
        bs_price = 8.0
        variance = fetcher.calculate_variance_percentage(current_price, bs_price)
        expected_variance = 25.0  # (10-8)/8 * 100
        
        if abs(variance - expected_variance) < 0.1:
            print(f"   ✅ Variance calculation correct: {variance:.1f}%")
        else:
            print(f"   ❌ Variance calculation incorrect: got {variance:.1f}%, expected {expected_variance:.1f}%")
            return False
    except Exception as e:
        print(f"   ❌ Variance calculation failed: {e}")
        return False
    
    # Test database operations
    print("7. Testing database operations...")
    try:
        summary = fetcher.get_analysis_summary()
        print(f"   ✅ Database summary retrieved: {summary.get('total_options', 0)} total options")
    except Exception as e:
        print(f"   ❌ Database operations failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The option analysis functionality is working correctly.")
    return True

def test_small_analysis():
    """Test a small analysis with one symbol"""
    
    print("\n🔍 Testing Small Analysis")
    print("=" * 30)
    
    try:
        fetcher = OptionDataFetcher(risk_free_rate=0.05)
        
        # Test with just one symbol
        symbols = ['AAPL']
        print(f"Analyzing {symbols[0]} options...")
        
        results = fetcher.fetch_and_store_options(symbols, variance_threshold=25.0)
        
        print(f"✅ Analysis complete!")
        print(f"   Total options processed: {results['total_options_processed']}")
        print(f"   High variance options found: {len(results['high_variance_options'])}")
        print(f"   Errors encountered: {len(results['errors'])}")
        
        if results['high_variance_options']:
            print(f"\n📊 Sample high variance option:")
            sample = results['high_variance_options'][0]
            print(f"   Symbol: {sample['symbol']}")
            print(f"   Type: {sample['option_type']}")
            print(f"   Strike: ${sample['strike']:.2f}")
            print(f"   Current: ${sample['current_price']:.2f}")
            print(f"   BS Price: ${sample['black_scholes_price']:.2f}")
            print(f"   Variance: {sample['variance_percentage']:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Small analysis failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting Option Analysis Tests...\n")
    
    # Run basic functionality tests
    basic_tests_passed = test_option_analysis()
    
    if basic_tests_passed:
        # Run small analysis test
        analysis_test_passed = test_small_analysis()
        
        if analysis_test_passed:
            print("\n🎯 All tests completed successfully!")
            print("The option analysis system is ready to use.")
            print("\nYou can now:")
            print("1. Run the CLI: python option_analyzer_cli.py --symbols AAPL TSLA")
            print("2. Use the Streamlit app: streamlit run app.py")
            print("3. Import and use the OptionDataFetcher class in your own code")
        else:
            print("\n❌ Analysis test failed. Check the error messages above.")
            sys.exit(1)
    else:
        print("\n❌ Basic functionality tests failed. Check the error messages above.")
        sys.exit(1) 