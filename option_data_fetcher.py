import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
from models import SessionLocal, YFinanceOption
from black_scholes import black_scholes_price
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptionDataFetcher:
    def __init__(self, risk_free_rate: float = 0.05):
        """
        Initialize the OptionDataFetcher
        
        Args:
            risk_free_rate (float): Risk-free interest rate (default: 5%)
        """
        self.risk_free_rate = risk_free_rate
        
    def get_risk_free_rate(self) -> float:
        """
        Get current risk-free rate (simplified - using 3-month Treasury yield)
        """
        try:
            # Try to get 3-month Treasury yield as risk-free rate
            treasury = yf.Ticker("^IRX")
            rate = treasury.info.get('regularMarketPrice', 0.05) / 100
            return max(rate, 0.01)  # Minimum 1%
        except:
            return self.risk_free_rate
    
    def fetch_stock_data(self, symbol: str) -> Dict:
        """
        Fetch current stock data
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            Dict: Stock information
        """
        try:
            ticker = yf.Ticker(symbol)
            # Use history method which is more reliable - try 5 days to get recent data
            hist = ticker.history(period="5d")
            
            if hist.empty:
                logger.error(f"No price data found for {symbol}")
                return None
            
            current_price = hist['Close'].iloc[-1]
            
            return {
                'current_price': current_price,
                'market_cap': 0,  # Not available via history
                'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0,
                'dividend_yield': 0  # Not available via history
            }
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def fetch_options_data(self, symbol: str, expiration_date: Optional[str] = None) -> Tuple[List, List]:
        """
        Fetch options data for a given symbol using proven yfinance approach
        
        Args:
            symbol (str): Stock symbol
            expiration_date (str): Specific expiration date (optional)
            
        Returns:
            Tuple[List, List]: (calls_data, puts_data)
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get available expirations
            expirations = ticker.options
            if not expirations:
                logger.warning(f"No options expirations found for {symbol}")
                return [], []
            
            # Limit to first few expirations to avoid too many API calls
            max_expirations = 3
            expirations_to_use = expirations[:max_expirations]
            
            all_calls = []
            all_puts = []
            
            for exp in expirations_to_use:
                try:
                    logger.info(f"Fetching options for {symbol} expiration {exp}...")
                    options = ticker.option_chain(exp)
                    
                    # Process calls
                    if not options.calls.empty:
                        calls_df = options.calls.copy()
                        calls_df['expiration'] = exp
                        # Fix yfinance date bug by adding 1 day
                        calls_df['expiration'] = pd.to_datetime(exp) + timedelta(days=1)
                        calls_data = calls_df.to_dict('records')
                        all_calls.extend(calls_data)
                    
                    # Process puts
                    if not options.puts.empty:
                        puts_df = options.puts.copy()
                        puts_df['expiration'] = exp
                        # Fix yfinance date bug by adding 1 day
                        puts_df['expiration'] = pd.to_datetime(exp) + timedelta(days=1)
                        puts_data = puts_df.to_dict('records')
                        all_puts.extend(puts_data)
                    
                    # Add delay between API calls
                    time.sleep(1)
                    
                except Exception as e:
                    logger.warning(f"Error fetching options for {symbol} expiration {exp}: {e}")
                    continue
            
            logger.info(f"✅ Fetched {len(all_calls)} calls and {len(all_puts)} puts for {symbol}")
            return all_calls, all_puts
            
        except Exception as e:
            logger.error(f"Error fetching options data for {symbol}: {e}")
            return [], []
    
    def calculate_time_to_expiry(self, expiration_date: str) -> float:
        """
        Calculate time to expiry in years
        
        Args:
            expiration_date (str): Expiration date string
            
        Returns:
            float: Time to expiry in years
        """
        try:
            exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
            current_date = datetime.now()
            time_diff = exp_date - current_date
            return max(time_diff.days / 365.25, 0.001)  # Minimum 0.001 years
        except:
            return 0.1  # Default to 0.1 years
    
    def calculate_black_scholes_for_option(self, option_data: Dict, stock_price: float, 
                                         time_to_expiry: float, option_type: str) -> float:
        """
        Calculate Black-Scholes price for an option
        
        Args:
            option_data (Dict): Option data from yfinance
            stock_price (float): Current stock price
            time_to_expiry (float): Time to expiry in years
            option_type (str): 'call' or 'put'
            
        Returns:
            float: Black-Scholes price
        """
        try:
            strike = option_data.get('strike', 0)
            implied_vol = option_data.get('impliedVolatility', 0.3)
            
            if strike <= 0 or implied_vol <= 0:
                return 0.0
            
            # Use mid-price for current option price
            bid = option_data.get('bid', 0)
            ask = option_data.get('ask', 0)
            current_price = (bid + ask) / 2 if bid > 0 and ask > 0 else option_data.get('lastPrice', 0)
            
            # Calculate Black-Scholes price
            bs_price = black_scholes_price(
                S=stock_price,
                K=strike,
                T=time_to_expiry,
                r=self.risk_free_rate,
                sigma=implied_vol,
                option_type=option_type
            )
            
            return bs_price
            
        except Exception as e:
            logger.error(f"Error calculating Black-Scholes price: {e}")
            return 0.0
    
    def calculate_variance_percentage(self, current_price: float, black_scholes_price: float) -> float:
        """
        Calculate variance percentage between current and Black-Scholes price
        
        Args:
            current_price (float): Current option price
            black_scholes_price (float): Black-Scholes calculated price
            
        Returns:
            float: Variance percentage
        """
        if black_scholes_price <= 0:
            return 0.0
        
        # Handle edge cases where Black-Scholes price is very small
        if black_scholes_price < 0.01:  # Less than 1 cent
            if current_price < 0.01:
                return 0.0  # Both prices are very small, no meaningful variance
            else:
                return 1000.0  # Cap at 1000% for very small BS prices
        
        variance = abs(current_price - black_scholes_price) / black_scholes_price * 100
        
        # Cap variance at 1000% to avoid extreme values
        return min(variance, 1000.0)
    
    def store_option_data(self, symbol: str, option_data: Dict, option_type: str, 
                         expiration_date, stock_data: Dict) -> bool:
        """
        Store option data in database
        
        Args:
            symbol (str): Stock symbol
            option_data (Dict): Option data from yfinance
            option_type (str): 'call' or 'put'
            expiration_date (str): Expiration date
            stock_data (Dict): Stock information
        """
        session = None
        try:
            session = SessionLocal()
            
            # Handle expiration date (can be string or datetime from yfinance)
            if isinstance(expiration_date, str):
                if not expiration_date or expiration_date.strip() == '':
                    logger.warning(f"Skipping {symbol} {option_type} - empty expiration date")
                    return False
                try:
                    exp_date = datetime.strptime(expiration_date, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Skipping {symbol} {option_type} - invalid expiration date format: {expiration_date}")
                    return False
            elif isinstance(expiration_date, pd.Timestamp):
                exp_date = expiration_date.to_pydatetime()
            else:
                exp_date = expiration_date
            
            # Check if expiration date is in the past or too old (more than 2 years)
            current_date = datetime.now()
            if exp_date < current_date:
                logger.debug(f"Skipping {symbol} {option_type} - expired: {exp_date}")
                return False
            if (exp_date - current_date).days > 730:  # More than 2 years
                logger.debug(f"Skipping {symbol} {option_type} - too far in future: {exp_date}")
                return False
            
            # Calculate time to expiry
            time_to_expiry = self.calculate_time_to_expiry(exp_date.strftime('%Y-%m-%d'))
            
            # Get current option price
            bid = option_data.get('bid', 0)
            ask = option_data.get('ask', 0)
            current_price = (bid + ask) / 2 if bid > 0 and ask > 0 else option_data.get('lastPrice', 0)
            
            # Skip if no valid price or price is too low
            if current_price <= 0:
                logger.warning(f"Skipping {symbol} {option_type} - no valid price")
                return False
            
            # Skip options with zero or negative prices (allow any positive price)
            if current_price <= 0:
                logger.debug(f"Skipping {symbol} {option_type} - price too low: ${current_price:.4f}")
                return False
            
            # Skip options with zero volume (allow any volume > 0)
            volume = option_data.get('volume', 0)
            if volume <= 0:
                logger.debug(f"Skipping {symbol} {option_type} - zero volume: {volume}")
                return False
            
            # Calculate Black-Scholes price
            black_scholes_price = self.calculate_black_scholes_for_option(
                option_data, stock_data['current_price'], time_to_expiry, option_type
            )
            
            # Skip if Black-Scholes calculation failed
            if black_scholes_price <= 0:
                logger.warning(f"Skipping {symbol} {option_type} - invalid Black-Scholes price: {black_scholes_price}")
                return False
            
            # Calculate variance
            variance_percentage = self.calculate_variance_percentage(current_price, black_scholes_price)
            
            # Log some sample calculations for debugging
            if symbol in ['AAPL', 'TSLA', 'SPY'] and option_type == 'call':
                logger.info(f"Sample calculation for {symbol} {option_type}: "
                          f"Current=${current_price:.4f}, BS=${black_scholes_price:.4f}, "
                          f"Variance={variance_percentage:.1f}%")
            
            # Log successful storage
            logger.debug(f"✅ Stored {symbol} {option_type} - Strike: ${option_data.get('strike', 0):.2f}, "
                        f"Price: ${current_price:.4f}, Volume: {volume}")
            
            # Create database record
            option_record = YFinanceOption(
                symbol=symbol,
                contractSymbol=option_data.get('contractSymbol', ''),
                strike=option_data.get('strike', 0),
                lastPrice=option_data.get('lastPrice', 0),
                bid=option_data.get('bid', 0),
                ask=option_data.get('ask', 0),
                change=option_data.get('change', 0),
                percentChange=option_data.get('percentChange', 0),
                volume=option_data.get('volume', 0),
                openInterest=option_data.get('openInterest', 0),
                impliedVolatility=option_data.get('impliedVolatility', 0),
                inTheMoney=option_data.get('inTheMoney', False),
                lastTradeDate=option_data.get('lastTradeDate', None),
                option_type=option_type,
                expiration_date=exp_date,
                current_stock_price=stock_data['current_price'],
                risk_free_rate=self.risk_free_rate,
                time_to_expiry=time_to_expiry,
                black_scholes_price=black_scholes_price,
                variance_percentage=variance_percentage
            )
            
            session.add(option_record)
            session.commit()
            return True
            
        except ValueError as e:
            logger.error(f"Error parsing expiration date '{expiration_date}' for {symbol} {option_type}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error storing option data for {symbol} {option_type}: {e}")
            return False
        finally:
            if session:
                try:
                    session.rollback()
                except:
                    pass
                session.close()
            return False
    
    def fetch_and_store_options(self, symbols: List[str], variance_threshold: float = 25.0) -> Dict:
        """
        Fetch and store options data for multiple symbols
        
        Args:
            symbols (List[str]): List of stock symbols
            variance_threshold (float): Minimum variance percentage to report
            
        Returns:
            Dict: Summary of results
        """
        # Clean up old data first
        self.cleanup_old_data()
        
        results = {
            'total_api_calls_made': 0,
            'total_api_calls_successful': 0,
            'total_options_fetched': 0,
            'total_options_processed': 0,
            'total_options_stored': 0,
            'high_variance_options': [],
            'errors': []
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Processing {symbol}...")
                
                # Track API call for stock data
                results['total_api_calls_made'] += 1
                stock_data = self.fetch_stock_data(symbol)
                if stock_data and stock_data['current_price'] > 0:
                    results['total_api_calls_successful'] += 1
                    logger.info(f"✅ Stock data fetched for {symbol}: ${stock_data['current_price']:.2f}")
                else:
                    results['errors'].append(f"No valid stock data for {symbol}")
                    continue
                
                # Add longer delay to avoid rate limiting
                logger.info(f"⏳ Waiting 5 seconds to avoid rate limiting...")
                time.sleep(5)
                
                # Track API call for options data
                results['total_api_calls_made'] += 1
                calls_data, puts_data = self.fetch_options_data(symbol)
                total_options_fetched = len(calls_data) + len(puts_data)
                results['total_options_fetched'] += total_options_fetched
                results['total_api_calls_successful'] += 1
                
                logger.info(f"📊 Fetched {len(calls_data)} calls and {len(puts_data)} puts for {symbol}")
                
                # Process calls
                calls_processed = 0
                for call_data in calls_data:
                    try:
                        expiration_date = call_data.get('expiration', '')
                        if expiration_date:  # Only process if we have a valid expiration date
                            if self.store_option_data(symbol, call_data, 'call', 
                                                     expiration_date, stock_data):
                                calls_processed += 1
                                results['total_options_processed'] += 1
                    except Exception as e:
                        results['errors'].append(f"Error processing call for {symbol}: {e}")
                
                # Process puts
                puts_processed = 0
                for put_data in puts_data:
                    try:
                        expiration_date = put_data.get('expiration', '')
                        if expiration_date:  # Only process if we have a valid expiration date
                            if self.store_option_data(symbol, put_data, 'put', 
                                                     expiration_date, stock_data):
                                puts_processed += 1
                                results['total_options_processed'] += 1
                    except Exception as e:
                        results['errors'].append(f"Error processing put for {symbol}: {e}")
                
                logger.info(f"✅ Processed {calls_processed} calls and {puts_processed} puts for {symbol}")
                
                # Log filtering summary
                total_fetched = len(calls_data) + len(puts_data)
                total_processed = calls_processed + puts_processed
                if total_fetched > 0:
                    filter_rate = (total_fetched - total_processed) / total_fetched * 100
                    logger.info(f"📊 Filtering summary for {symbol}: {total_processed}/{total_fetched} options stored ({filter_rate:.1f}% filtered out)")
                
            except Exception as e:
                results['errors'].append(f"Error processing {symbol}: {e}")
        
        # Count total options stored in database
        try:
            session = SessionLocal()
            results['total_options_stored'] = session.query(YFinanceOption).count()
            session.close()
        except Exception as e:
            logger.error(f"Error counting stored options: {e}")
        
        # Get high variance options from stored data
        results['high_variance_options'] = self.get_high_variance_options(variance_threshold)
        
        return results
    
    def get_high_variance_options(self, variance_threshold: float = 25.0) -> List[Dict]:
        """
        Get options with variance above threshold
        
        Args:
            variance_threshold (float): Minimum variance percentage
            
        Returns:
            List[Dict]: List of high variance options
        """
        try:
            session = SessionLocal()
            
            # Query for options with high variance
            high_variance_options = session.query(YFinanceOption).filter(
                YFinanceOption.variance_percentage >= variance_threshold,
                YFinanceOption.variance_percentage < 1000  # Exclude extreme values
            ).order_by(YFinanceOption.variance_percentage.desc()).all()
            
            # Convert to dictionaries
            options_list = []
            for option in high_variance_options:
                option_dict = {
                    'symbol': option.symbol,
                    'contract_symbol': option.contractSymbol,
                    'option_type': option.option_type,
                    'strike': option.strike,
                    'current_price': (option.bid + option.ask) / 2 if option.bid > 0 and option.ask > 0 else option.lastPrice,
                    'black_scholes_price': option.black_scholes_price,
                    'variance_percentage': option.variance_percentage,
                    'implied_volatility': option.impliedVolatility,
                    'time_to_expiry': option.time_to_expiry,
                    'volume': option.volume,
                    'open_interest': option.openInterest,
                    'expiration_date': option.expiration_date.strftime('%Y-%m-%d'),
                    'current_stock_price': option.current_stock_price
                }
                options_list.append(option_dict)
            
            session.close()
            return options_list
            
        except Exception as e:
            logger.error(f"Error getting high variance options: {e}")
            return []
    
    def cleanup_old_data(self, remove_all: bool = False):
        """
        Clean up old and invalid data from the database
        
        Args:
            remove_all (bool): If True, remove all data regardless of criteria
        """
        try:
            session = SessionLocal()
            
            if remove_all:
                # Remove all data
                total_count = session.query(YFinanceOption).count()
                session.query(YFinanceOption).delete()
                session.commit()
                session.close()
                logger.info(f"Removed all {total_count} options from database")
                return
            
            # Delete expired options
            current_date = datetime.now()
            expired_count = session.query(YFinanceOption).filter(
                YFinanceOption.expiration_date < current_date
            ).delete()
            
            # Delete options with very old expiration dates (more than 2 years in future)
            future_date = current_date + timedelta(days=730)
            old_future_count = session.query(YFinanceOption).filter(
                YFinanceOption.expiration_date > future_date
            ).delete()
            
            # Delete options with zero or negative prices
            invalid_price_count = session.query(YFinanceOption).filter(
                YFinanceOption.lastPrice <= 0
            ).delete()
            
            # Delete options with very low volume (less than 10)
            low_volume_count = session.query(YFinanceOption).filter(
                YFinanceOption.volume < 10
            ).delete()
            
            session.commit()
            session.close()
            
            logger.info(f"Cleaned up database: {expired_count} expired, {old_future_count} old future, "
                       f"{invalid_price_count} invalid prices, {low_volume_count} low volume")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_analysis_summary(self) -> Dict:
        """
        Get summary statistics of stored options data
        
        Returns:
            Dict: Summary statistics
        """
        try:
            session = SessionLocal()
            
            total_options = session.query(YFinanceOption).count()
            calls_count = session.query(YFinanceOption).filter(YFinanceOption.option_type == 'call').count()
            puts_count = session.query(YFinanceOption).filter(YFinanceOption.option_type == 'put').count()
            
            # Get average variance (exclude extreme values)
            avg_variance_result = session.query(YFinanceOption.variance_percentage).filter(
                YFinanceOption.variance_percentage > 0,
                YFinanceOption.variance_percentage < 1000  # Exclude extreme values
            ).all()
            avg_variance = sum([row[0] for row in avg_variance_result]) / len(avg_variance_result) if avg_variance_result else 0
            
            # Get unique symbols
            unique_symbols = session.query(YFinanceOption.symbol).distinct().count()
            
            # Get count of high variance options (for consistency)
            high_variance_count = session.query(YFinanceOption).filter(
                YFinanceOption.variance_percentage >= 25.0
            ).count()
            
            session.close()
            
            return {
                'total_options': total_options,
                'calls_count': calls_count,
                'puts_count': puts_count,
                'average_variance': avg_variance or 0,
                'unique_symbols': unique_symbols,
                'high_variance_count': high_variance_count
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis summary: {e}")
            return {}

def main():
    """
    Main function to demonstrate usage
    """
    # Example usage
    fetcher = OptionDataFetcher()
    
    # Popular stocks to analyze
    symbols = ['AAPL', 'TSLA', 'SPY', 'QQQ', 'NVDA', 'MSFT', 'GOOGL', 'AMZN']
    
    print("Fetching and analyzing options data...")
    results = fetcher.fetch_and_store_options(symbols, variance_threshold=25.0)
    
    print(f"\nResults:")
    print(f"Total options processed: {results['total_options_processed']}")
    print(f"High variance options found: {len(results['high_variance_options'])}")
    
    if results['high_variance_options']:
        print(f"\nTop 10 options with >25% variance:")
        for i, option in enumerate(results['high_variance_options'][:10]):
            print(f"{i+1}. {option['symbol']} {option['option_type'].upper()} "
                  f"Strike: ${option['strike']:.2f} "
                  f"Current: ${option['current_price']:.2f} "
                  f"BS: ${option['black_scholes_price']:.2f} "
                  f"Variance: {option['variance_percentage']:.1f}%")
    
    if results['errors']:
        print(f"\nErrors encountered: {len(results['errors'])}")
        for error in results['errors'][:5]:  # Show first 5 errors
            print(f"- {error}")

if __name__ == "__main__":
    main() 