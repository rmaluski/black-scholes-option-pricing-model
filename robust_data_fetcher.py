#!/usr/bin/env python3
"""
Robust financial data fetcher with multiple fallback sources
"""

import yfinance as yf
import requests
import time
from datetime import datetime, timedelta
import numpy as np

class RobustDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_stock_price(self, symbol, max_retries=3):
        """Get stock price with multiple retry strategies"""
        for attempt in range(max_retries):
            try:
                # Method 1: Try yfinance with different periods
                periods = ["1d", "5d", "1mo"]
                for period in periods:
                    try:
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(period=period)
                        if not data.empty:
                            price = data["Close"].iloc[-1]
                            if price > 0:
                                print(f"✅ Got {symbol} price: ${price:.2f} (period: {period})")
                                return price
                    except Exception as e:
                        print(f"Attempt {attempt + 1}, period {period} failed: {e}")
                        continue
                
                # Method 2: Try with delay and different user agent
                time.sleep(2)
                ticker = yf.Ticker(symbol)
                ticker._base_url = "https://query1.finance.yahoo.com"
                data = ticker.history(period="1d")
                if not data.empty:
                    price = data["Close"].iloc[-1]
                    if price > 0:
                        print(f"✅ Got {symbol} price: ${price:.2f} (retry)")
                        return price
                        
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(3)
        
        print(f"❌ Could not fetch {symbol} price after {max_retries} attempts")
        return None
    
    def get_treasury_yield(self, max_retries=3):
        """Get 10-year Treasury yield with fallbacks"""
        symbols = ["^TNX", "^TYX", "TNX"]
        
        for symbol in symbols:
            for attempt in range(max_retries):
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="5d")
                    if not data.empty:
                        yield_value = data["Close"].iloc[-1] / 100
                        if yield_value > 0:
                            print(f"✅ Got Treasury yield: {yield_value:.4%} from {symbol}")
                            return yield_value
                except Exception as e:
                    print(f"Treasury attempt {attempt + 1} for {symbol} failed: {e}")
                    time.sleep(2)
        
        print("❌ Could not fetch Treasury yield, using default")
        return 0.04  # Default 4%
    
    def get_vix(self, max_retries=3):
        """Get VIX with fallbacks"""
        symbols = ["^VIX", "VIX"]
        
        for symbol in symbols:
            for attempt in range(max_retries):
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="5d")
                    if not data.empty:
                        vix_value = data["Close"].iloc[-1] / 100
                        if vix_value > 0:
                            print(f"✅ Got VIX: {vix_value:.4%} from {symbol}")
                            return vix_value
                except Exception as e:
                    print(f"VIX attempt {attempt + 1} for {symbol} failed: {e}")
                    time.sleep(2)
        
        print("❌ Could not fetch VIX, using default")
        return 0.20  # Default 20%
    
    def get_options_chain(self, symbol, expiry_date, max_retries=3):
        """Get options chain with retries"""
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                opt_chain = ticker.option_chain(expiry_date.strftime("%Y-%m-%d"))
                if opt_chain and (not opt_chain.calls.empty or not opt_chain.puts.empty):
                    print(f"✅ Got options chain for {symbol}")
                    return opt_chain
            except Exception as e:
                print(f"Options attempt {attempt + 1} failed: {e}")
                time.sleep(3)
        
        print(f"❌ Could not fetch options for {symbol}")
        return None

# Test the robust fetcher
if __name__ == "__main__":
    fetcher = RobustDataFetcher()
    
    print("Testing robust data fetcher...")
    
    # Test stock price
    price = fetcher.get_stock_price("AAPL")
    print(f"AAPL Price: ${price:.2f}" if price else "Failed")
    
    # Test Treasury yield
    yield_val = fetcher.get_treasury_yield()
    print(f"Treasury Yield: {yield_val:.4%}")
    
    # Test VIX
    vix_val = fetcher.get_vix()
    print(f"VIX: {vix_val:.4%}")
    
    # Test options
    expiry = datetime.now() + timedelta(days=30)
    options = fetcher.get_options_chain("AAPL", expiry)
    if options:
        print(f"Options: {len(options.calls)} calls, {len(options.puts)} puts")
    else:
        print("Options: Failed") 