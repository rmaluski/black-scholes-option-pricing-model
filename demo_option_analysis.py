#!/usr/bin/env python3
"""
Demo script for option analysis functionality with mock data
"""

import sys
import os
from datetime import datetime, timedelta
from models import init_db, YFinanceOption, SessionLocal
from option_data_fetcher import OptionDataFetcher
import pandas as pd

def create_mock_data():
    """Create mock options data for demonstration"""
    
    print("🎭 Creating mock options data for demonstration...")
    
    # Initialize database
    init_db()
    
    # Create mock data
    mock_options = [
        # AAPL Options
        {
            'symbol': 'AAPL',
            'contractSymbol': 'AAPL240119C00150000',
            'strike': 150.0,
            'lastPrice': 5.20,
            'bid': 5.15,
            'ask': 5.25,
            'change': 0.30,
            'percentChange': 6.12,
            'volume': 1500,
            'openInterest': 2500,
            'impliedVolatility': 0.250,
            'inTheMoney': False,
            'lastTradeDate': datetime.now() - timedelta(hours=2),
            'option_type': 'call',
            'expiration_date': datetime(2024, 1, 19),
            'current_stock_price': 145.50,
            'risk_free_rate': 0.05,
            'time_to_expiry': 0.1,
            'black_scholes_price': 3.80,
            'variance_percentage': 36.8
        },
        {
            'symbol': 'AAPL',
            'contractSymbol': 'AAPL240119P00140000',
            'strike': 140.0,
            'lastPrice': 2.80,
            'bid': 2.75,
            'ask': 2.85,
            'change': -0.15,
            'percentChange': -5.08,
            'volume': 800,
            'openInterest': 1200,
            'impliedVolatility': 0.280,
            'inTheMoney': True,
            'lastTradeDate': datetime.now() - timedelta(hours=1),
            'option_type': 'put',
            'expiration_date': datetime(2024, 1, 19),
            'current_stock_price': 145.50,
            'risk_free_rate': 0.05,
            'time_to_expiry': 0.1,
            'black_scholes_price': 2.10,
            'variance_percentage': 33.3
        },
        # TSLA Options
        {
            'symbol': 'TSLA',
            'contractSymbol': 'TSLA240119C00200000',
            'strike': 200.0,
            'lastPrice': 8.50,
            'bid': 8.40,
            'ask': 8.60,
            'change': 0.75,
            'percentChange': 9.68,
            'volume': 2200,
            'openInterest': 3500,
            'impliedVolatility': 0.320,
            'inTheMoney': False,
            'lastTradeDate': datetime.now() - timedelta(hours=3),
            'option_type': 'call',
            'expiration_date': datetime(2024, 1, 19),
            'current_stock_price': 185.00,
            'risk_free_rate': 0.05,
            'time_to_expiry': 0.1,
            'black_scholes_price': 6.20,
            'variance_percentage': 37.1
        },
        {
            'symbol': 'TSLA',
            'contractSymbol': 'TSLA240119P00180000',
            'strike': 180.0,
            'lastPrice': 4.20,
            'bid': 4.15,
            'ask': 4.25,
            'change': 0.20,
            'percentChange': 5.00,
            'volume': 1200,
            'openInterest': 1800,
            'impliedVolatility': 0.350,
            'inTheMoney': True,
            'lastTradeDate': datetime.now() - timedelta(hours=2),
            'option_type': 'put',
            'expiration_date': datetime(2024, 1, 19),
            'current_stock_price': 185.00,
            'risk_free_rate': 0.05,
            'time_to_expiry': 0.1,
            'black_scholes_price': 3.10,
            'variance_percentage': 35.5
        },
        # SPY Options
        {
            'symbol': 'SPY',
            'contractSymbol': 'SPY240119C00450000',
            'strike': 450.0,
            'lastPrice': 3.80,
            'bid': 3.75,
            'ask': 3.85,
            'change': 0.25,
            'percentChange': 7.04,
            'volume': 5000,
            'openInterest': 8000,
            'impliedVolatility': 0.180,
            'inTheMoney': False,
            'lastTradeDate': datetime.now() - timedelta(hours=1),
            'option_type': 'call',
            'expiration_date': datetime(2024, 1, 19),
            'current_stock_price': 445.00,
            'risk_free_rate': 0.05,
            'time_to_expiry': 0.1,
            'black_scholes_price': 2.90,
            'variance_percentage': 31.0
        },
        # NVDA Options
        {
            'symbol': 'NVDA',
            'contractSymbol': 'NVDA240119C00480000',
            'strike': 480.0,
            'lastPrice': 12.50,
            'bid': 12.40,
            'ask': 12.60,
            'change': 1.20,
            'percentChange': 10.62,
            'volume': 1800,
            'openInterest': 2800,
            'impliedVolatility': 0.400,
            'inTheMoney': False,
            'lastTradeDate': datetime.now() - timedelta(hours=4),
            'option_type': 'call',
            'expiration_date': datetime(2024, 1, 19),
            'current_stock_price': 465.00,
            'risk_free_rate': 0.05,
            'time_to_expiry': 0.1,
            'black_scholes_price': 9.20,
            'variance_percentage': 35.9
        }
    ]
    
    # Store mock data in database
    session = SessionLocal()
    
    try:
        for option_data in mock_options:
            option_record = YFinanceOption(**option_data)
            session.add(option_record)
        
        session.commit()
        print(f"✅ Created {len(mock_options)} mock option records")
        
    except Exception as e:
        print(f"❌ Error creating mock data: {e}")
        session.rollback()
    finally:
        session.close()

def demo_analysis():
    """Demonstrate the analysis functionality"""
    
    print("\n🔍 Demonstrating Option Analysis")
    print("=" * 50)
    
    # Create fetcher
    fetcher = OptionDataFetcher(risk_free_rate=0.05)
    
    # Get high variance options
    high_variance_options = fetcher.get_high_variance_options(variance_threshold=25.0)
    
    if high_variance_options:
        print(f"\n📊 Found {len(high_variance_options)} options with >25% variance:")
        print()
        
        # Create DataFrame for display
        df = pd.DataFrame(high_variance_options)
        
        # Format the data for better display
        display_df = df[['symbol', 'option_type', 'strike', 'current_price', 
                       'black_scholes_price', 'variance_percentage', 'implied_volatility',
                       'volume', 'open_interest', 'expiration_date']].copy()
        
        display_df.columns = ['Symbol', 'Type', 'Strike', 'Current', 'BS Price', 
                            'Variance %', 'IV', 'Volume', 'OI', 'Expiry']
        
        # Format numeric columns
        display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
        display_df['Current'] = display_df['Current'].apply(lambda x: f"${x:.2f}")
        display_df['BS Price'] = display_df['BS Price'].apply(lambda x: f"${x:.2f}")
        display_df['Variance %'] = display_df['Variance %'].apply(lambda x: f"{x:.1f}%")
        display_df['IV'] = display_df['IV'].apply(lambda x: f"{x:.3f}")
        
        print(display_df.to_string(index=False))
        
        # Show summary statistics
        summary = fetcher.get_analysis_summary()
        if summary:
            print(f"\n📈 Analysis Summary:")
            print(f"   Total Options: {summary.get('total_options', 0)}")
            print(f"   Calls: {summary.get('calls_count', 0)}")
            print(f"   Puts: {summary.get('puts_count', 0)}")
            print(f"   Average Variance: {summary.get('average_variance', 0):.1f}%")
            print(f"   Unique Symbols: {summary.get('unique_symbols', 0)}")
        
        # Show potential opportunities
        print(f"\n🎯 Potential Trading Opportunities:")
        for option in high_variance_options[:3]:  # Show top 3
            symbol = option['symbol']
            option_type = option['option_type'].upper()
            strike = option['strike']
            current = option['current_price']
            bs_price = option['black_scholes_price']
            variance = option['variance_percentage']
            
            if current > bs_price:
                action = "SHORT"  # Overpriced
                reason = f"Market price (${current:.2f}) > BS price (${bs_price:.2f})"
            else:
                action = "LONG"   # Underpriced
                reason = f"Market price (${current:.2f}) < BS price (${bs_price:.2f})"
            
            print(f"   {action} {symbol} {option_type} ${strike:.0f} - {variance:.1f}% variance")
            print(f"      {reason}")
            print()
        
    else:
        print("No high variance options found in the database.")
    
    return high_variance_options

def demo_cli_usage():
    """Show how to use the CLI"""
    
    print("\n💻 CLI Usage Examples")
    print("=" * 30)
    
    print("1. Initialize database:")
    print("   python option_analyzer_cli.py --init-db")
    print()
    
    print("2. Analyze specific symbols:")
    print("   python option_analyzer_cli.py --symbols AAPL TSLA SPY")
    print()
    
    print("3. Use custom variance threshold:")
    print("   python option_analyzer_cli.py --symbols NVDA AMD --threshold 30")
    print()
    
    print("4. Show existing analysis:")
    print("   python option_analyzer_cli.py --show-only --threshold 20")
    print()
    
    print("5. Save results to CSV:")
    print("   python option_analyzer_cli.py --symbols AAPL MSFT --output results.csv")
    print()

def main():
    """Main demo function"""
    
    print("🎪 Option Analysis System Demo")
    print("=" * 50)
    print("This demo shows how the option analysis system works with mock data.")
    print("In real usage, it would fetch live data from yfinance.")
    print()
    
    # Create mock data
    create_mock_data()
    
    # Demonstrate analysis
    high_variance_options = demo_analysis()
    
    # Show CLI usage
    demo_cli_usage()
    
    print("🎉 Demo complete!")
    print("\nTo use with real data:")
    print("1. Run: python option_analyzer_cli.py --symbols AAPL TSLA")
    print("2. Or use the web interface: streamlit run app.py")
    print("3. Note: Real data fetching may be rate-limited by yfinance")

if __name__ == "__main__":
    main() 