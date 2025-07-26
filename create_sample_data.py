#!/usr/bin/env python3
"""
Create realistic sample options data for testing
"""

from datetime import datetime, timedelta
from models import init_db, YFinanceOption, SessionLocal
import random

def create_realistic_sample_data():
    """Create realistic sample options data"""
    
    print("Creating realistic sample options data...")
    
    # Initialize database
    init_db()
    
    # Current date
    current_date = datetime.now()
    
    # Sample data for popular stocks
    sample_data = [
        {
            'symbol': 'SPY',
            'current_price': 445.50,
            'options': [
                {'strike': 440, 'type': 'call', 'price': 8.50, 'bs_price': 6.20, 'volume': 1500, 'iv': 0.18},
                {'strike': 440, 'type': 'put', 'price': 3.20, 'bs_price': 2.80, 'volume': 1200, 'iv': 0.19},
                {'strike': 450, 'type': 'call', 'price': 3.80, 'bs_price': 2.90, 'volume': 2000, 'iv': 0.17},
                {'strike': 450, 'type': 'put', 'price': 8.20, 'bs_price': 7.50, 'volume': 1800, 'iv': 0.20},
                {'strike': 460, 'type': 'call', 'price': 1.20, 'bs_price': 0.95, 'volume': 2500, 'iv': 0.16},
                {'strike': 460, 'type': 'put', 'price': 15.80, 'bs_price': 14.20, 'volume': 900, 'iv': 0.21},
            ]
        },
        {
            'symbol': 'AAPL',
            'current_price': 175.30,
            'options': [
                {'strike': 170, 'type': 'call', 'price': 8.50, 'bs_price': 6.20, 'volume': 1800, 'iv': 0.25},
                {'strike': 170, 'type': 'put', 'price': 3.20, 'bs_price': 2.80, 'volume': 1500, 'iv': 0.26},
                {'strike': 175, 'type': 'call', 'price': 5.20, 'bs_price': 3.80, 'volume': 2200, 'iv': 0.24},
                {'strike': 175, 'type': 'put', 'price': 5.80, 'bs_price': 4.20, 'volume': 1900, 'iv': 0.27},
                {'strike': 180, 'type': 'call', 'price': 2.80, 'bs_price': 2.10, 'volume': 2800, 'iv': 0.23},
                {'strike': 180, 'type': 'put', 'price': 9.50, 'bs_price': 8.80, 'volume': 1200, 'iv': 0.28},
            ]
        },
        {
            'symbol': 'TSLA',
            'current_price': 185.00,
            'options': [
                {'strike': 180, 'type': 'call', 'price': 12.50, 'bs_price': 9.20, 'volume': 1600, 'iv': 0.40},
                {'strike': 180, 'type': 'put', 'price': 7.20, 'bs_price': 5.80, 'volume': 1400, 'iv': 0.42},
                {'strike': 190, 'type': 'call', 'price': 8.50, 'bs_price': 6.20, 'volume': 2000, 'iv': 0.38},
                {'strike': 190, 'type': 'put', 'price': 12.80, 'bs_price': 11.50, 'volume': 1100, 'iv': 0.44},
                {'strike': 200, 'type': 'call', 'price': 5.20, 'bs_price': 3.80, 'volume': 2500, 'iv': 0.36},
                {'strike': 200, 'type': 'put', 'price': 18.50, 'bs_price': 16.80, 'volume': 800, 'iv': 0.46},
            ]
        }
    ]
    
    # Create expiration dates (next few months)
    expiration_dates = [
        current_date + timedelta(days=30),   # 1 month
        current_date + timedelta(days=60),   # 2 months
        current_date + timedelta(days=90),   # 3 months
    ]
    
    session = SessionLocal()
    
    try:
        for stock_data in sample_data:
            symbol = stock_data['symbol']
            current_price = stock_data['current_price']
            
            for option_data in stock_data['options']:
                for exp_date in expiration_dates:
                    # Calculate time to expiry
                    time_to_expiry = (exp_date - current_date).days / 365.25
                    
                    # Calculate variance
                    variance = abs(option_data['price'] - option_data['bs_price']) / option_data['bs_price'] * 100
                    
                    # Create option record
                    option_record = YFinanceOption(
                        symbol=symbol,
                        contractSymbol=f"{symbol}{exp_date.strftime('%y%m%d')}{option_data['type'][0].upper()}{int(option_data['strike']*1000):08d}",
                        strike=option_data['strike'],
                        lastPrice=option_data['price'],
                        bid=option_data['price'] - 0.05,
                        ask=option_data['price'] + 0.05,
                        change=random.uniform(-0.5, 0.5),
                        percentChange=random.uniform(-5, 5),
                        volume=option_data['volume'],
                        openInterest=option_data['volume'] + random.randint(0, 500),
                        impliedVolatility=option_data['iv'],
                        inTheMoney=option_data['type'] == 'call' and current_price > option_data['strike'],
                        lastTradeDate=current_date - timedelta(hours=random.randint(1, 24)),
                        option_type=option_data['type'],
                        expiration_date=exp_date,
                        current_stock_price=current_price,
                        risk_free_rate=0.05,
                        time_to_expiry=time_to_expiry,
                        black_scholes_price=option_data['bs_price'],
                        variance_percentage=variance
                    )
                    
                    session.add(option_record)
        
        session.commit()
        print("✅ Sample data created successfully!")
        
        # Show summary
        total_options = session.query(YFinanceOption).count()
        calls_count = session.query(YFinanceOption).filter(YFinanceOption.option_type == 'call').count()
        puts_count = session.query(YFinanceOption).filter(YFinanceOption.option_type == 'put').count()
        
        print(f"Total options created: {total_options}")
        print(f"Calls: {calls_count}")
        print(f"Puts: {puts_count}")
        
        # Show some high variance options
        high_variance = session.query(YFinanceOption).filter(
            YFinanceOption.variance_percentage >= 25
        ).order_by(YFinanceOption.variance_percentage.desc()).limit(5).all()
        
        print(f"\nHigh variance options (≥25%):")
        for option in high_variance:
            print(f"  {option.symbol} {option.option_type.upper()} ${option.strike} "
                  f"Current: ${option.lastPrice:.2f} BS: ${option.black_scholes_price:.2f} "
                  f"Variance: {option.variance_percentage:.1f}%")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_realistic_sample_data() 