#!/usr/bin/env python3
"""
CLI interface for option analysis and variance detection
"""

import argparse
import sys
from typing import List
from option_data_fetcher import OptionDataFetcher
from models import init_db
import pandas as pd

def display_high_variance_options(options: List[dict], limit: int = 20, threshold: float = 25.0):
    """
    Display high variance options in a formatted table
    """
    if not options:
        print("No high variance options found.")
        return
    
    # Create DataFrame for better display
    df = pd.DataFrame(options)
    
    # Select and rename columns for display
    display_df = df[['symbol', 'option_type', 'strike', 'current_price', 
                     'black_scholes_price', 'variance_percentage', 'implied_volatility',
                     'volume', 'open_interest', 'expiration_date']].head(limit)
    
    display_df.columns = ['Symbol', 'Type', 'Strike', 'Current', 'BS Price', 
                         'Variance %', 'IV', 'Volume', 'OI', 'Expiry']
    
    # Format numeric columns
    display_df['Strike'] = display_df['Strike'].apply(lambda x: f"${x:.2f}")
    display_df['Current'] = display_df['Current'].apply(lambda x: f"${x:.2f}")
    display_df['BS Price'] = display_df['BS Price'].apply(lambda x: f"${x:.2f}")
    display_df['Variance %'] = display_df['Variance %'].apply(lambda x: f"{x:.1f}%")
    display_df['IV'] = display_df['IV'].apply(lambda x: f"{x:.3f}")
    
    print("\n" + "="*120)
    print(f"HIGH VARIANCE OPTIONS (>{threshold}% difference from Black-Scholes)")
    print("="*120)
    print(display_df.to_string(index=False))
    print("="*120)

def display_summary(summary: dict):
    """
    Display analysis summary
    """
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    print(f"Total Options Processed: {summary.get('total_options', 0):,}")
    print(f"Calls: {summary.get('calls_count', 0):,}")
    print(f"Puts: {summary.get('puts_count', 0):,}")
    print(f"Unique Symbols: {summary.get('unique_symbols', 0)}")
    print(f"Average Variance: {summary.get('average_variance', 0):.1f}%")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(
        description="Analyze options data from yfinance and identify high variance options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze popular stocks with default settings
  python option_analyzer_cli.py --symbols AAPL TSLA SPY QQQ

  # Analyze with custom variance threshold
  python option_analyzer_cli.py --symbols AAPL MSFT --threshold 30

  # Show only high variance options from existing data
  python option_analyzer_cli.py --show-only --threshold 20

  # Analyze specific symbols and save to CSV
  python option_analyzer_cli.py --symbols NVDA AMD --output results.csv
        """
    )
    
    parser.add_argument(
        '--symbols', 
        nargs='+', 
        default=['AAPL', 'TSLA', 'SPY', 'QQQ', 'NVDA', 'MSFT', 'GOOGL', 'AMZN'],
        help='Stock symbols to analyze (default: popular tech stocks)'
    )
    
    parser.add_argument(
        '--threshold', 
        type=float, 
        default=25.0,
        help='Variance threshold percentage (default: 25.0)'
    )
    
    parser.add_argument(
        '--show-only', 
        action='store_true',
        help='Show only high variance options from existing data (no new fetching)'
    )
    
    parser.add_argument(
        '--output', 
        type=str,
        help='Save high variance options to CSV file'
    )
    
    parser.add_argument(
        '--risk-free-rate', 
        type=float, 
        default=0.05,
        help='Risk-free interest rate (default: 0.05 = 5%)'
    )
    
    parser.add_argument(
        '--limit', 
        type=int, 
        default=20,
        help='Maximum number of high variance options to display (default: 20)'
    )
    
    parser.add_argument(
        '--init-db', 
        action='store_true',
        help='Initialize database tables'
    )
    
    parser.add_argument(
        '--cleanup', 
        action='store_true',
        help='Clean up old and invalid data from database'
    )
    
    parser.add_argument(
        '--create-sample', 
        action='store_true',
        help='Create realistic sample data for testing'
    )
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        init_db()
        print("Database initialized successfully!")
    
    # Clean up database if requested
    if args.cleanup:
        print("Cleaning up old data...")
        fetcher = OptionDataFetcher(risk_free_rate=args.risk_free_rate)
        fetcher.cleanup_old_data(remove_all=True)  # Remove all data to start fresh
        print("Database cleanup complete!")
        return
    
    # Create sample data if requested
    if args.create_sample:
        print("Creating sample data...")
        from create_sample_data import create_realistic_sample_data
        create_realistic_sample_data()
        return
    
    # Create fetcher instance
    fetcher = OptionDataFetcher(risk_free_rate=args.risk_free_rate)
    
    if args.show_only:
        # Show only existing data
        print("Fetching high variance options from database...")
        high_variance_options = fetcher.get_high_variance_options(args.threshold)
        
        if high_variance_options:
            display_high_variance_options(high_variance_options, args.limit, args.threshold)
            
            # Save to CSV if requested
            if args.output:
                df = pd.DataFrame(high_variance_options)
                df.to_csv(args.output, index=False)
                print(f"\nHigh variance options saved to {args.output}")
        else:
            print("No high variance options found in database.")
            
        # Show summary
        summary = fetcher.get_analysis_summary()
        display_summary(summary)
        
    else:
        # Fetch new data and analyze
        print(f"Analyzing options for symbols: {', '.join(args.symbols)}")
        print(f"Variance threshold: {args.threshold}%")
        print(f"Risk-free rate: {args.risk_free_rate:.1%}")
        print("\nFetching and analyzing options data...")
        
        results = fetcher.fetch_and_store_options(args.symbols, args.threshold)
        
        print(f"\nProcessing complete!")
        print(f"📊 API Call Summary:")
        print(f"  API calls made: {results['total_api_calls_made']}")
        print(f"  API calls successful: {results['total_api_calls_successful']}")
        print(f"  Success rate: {results['total_api_calls_successful']/results['total_api_calls_made']*100:.1f}%" if results['total_api_calls_made'] > 0 else "  Success rate: 0%")
        
        print(f"\n📈 Data Processing Summary:")
        print(f"  Options fetched from API: {results['total_options_fetched']}")
        print(f"  Options processed: {results['total_options_processed']}")
        print(f"  Options stored in database: {results['total_options_stored']}")
        print(f"  High variance options found: {len(results['high_variance_options'])}")
        
        if results['errors']:
            print(f"Errors encountered: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        # Display high variance options
        if results['high_variance_options']:
            display_high_variance_options(results['high_variance_options'], args.limit, args.threshold)
            
            # Save to CSV if requested
            if args.output:
                df = pd.DataFrame(results['high_variance_options'])
                df.to_csv(args.output, index=False)
                print(f"\nHigh variance options saved to {args.output}")
        
        # Show summary
        summary = fetcher.get_analysis_summary()
        display_summary(summary)

if __name__ == "__main__":
    main() 