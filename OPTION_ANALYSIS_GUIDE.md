# Option Analysis & Variance Detection Guide

## Overview

This system automatically identifies potentially mispriced options by comparing market prices with Black-Scholes theoretical values. It fetches real-time options data from yfinance, calculates Black-Scholes prices, and identifies options with significant variance (>25% by default).

## 🚀 Quick Start

### 1. Initialize Database

```bash
python option_analyzer_cli.py --init-db
```

### 2. Analyze Options

```bash
# Analyze popular stocks
python option_analyzer_cli.py --symbols AAPL TSLA SPY QQQ

# Use custom variance threshold
python option_analyzer_cli.py --symbols NVDA AMD --threshold 30

# Save results to CSV
python option_analyzer_cli.py --symbols AAPL MSFT --output results.csv
```

### 3. Web Interface

```bash
streamlit run app.py
```

Then navigate to the "Option Analysis" tab.

## 📊 Understanding the Results

### High Variance Options

- **Overpriced**: Market price > Black-Scholes price (potential short opportunity)
- **Underpriced**: Market price < Black-Scholes price (potential long opportunity)

### Example Output

```
HIGH VARIANCE OPTIONS (>25% difference from Black-Scholes)
========================================================================================================================
Symbol  Type  Strike   Current  BS Price  Variance %     IV  Volume    OI    Expiry
  AAPL  CALL   $150.00    $5.20     $3.80      36.8%  0.250    1500  2500  2024-01-19
  TSLA   PUT   $200.00    $8.50     $6.20      37.1%  0.320     800  1200  2024-01-19
```

### Key Metrics

- **Variance %**: Percentage difference between market and theoretical price
- **IV**: Implied Volatility
- **Volume**: Trading volume
- **OI**: Open Interest (liquidity indicator)

## 🔧 Configuration Options

### CLI Parameters

- `--symbols`: List of stock symbols to analyze
- `--threshold`: Minimum variance percentage (default: 25.0)
- `--risk-free-rate`: Risk-free interest rate (default: 0.05)
- `--output`: Save results to CSV file
- `--show-only`: Display existing data without fetching new data
- `--init-db`: Initialize database tables

### Risk-Free Rate

The system uses a 5% default risk-free rate. You can customize this:

- **Conservative**: 3-4% (Treasury bills)
- **Moderate**: 5-6% (current market rates)
- **Aggressive**: 7-8% (higher risk tolerance)

## 📈 Trading Strategy Considerations

### High Variance Doesn't Guarantee Mispricing

- Market may know something the model doesn't
- Earnings announcements, news events
- Liquidity constraints
- Market maker spreads

### Risk Management

1. **Check Liquidity**: High volume/open interest
2. **Verify Data**: Ensure current prices are accurate
3. **Consider Greeks**: Delta, gamma, theta exposure
4. **Position Sizing**: Don't risk more than 1-2% per trade
5. **Stop Losses**: Set appropriate exit points

### Example Analysis

```
🎯 Potential Trading Opportunities:
   SHORT TSLA CALL $200 - 37.1% variance
      Market price ($8.50) > BS price ($6.20)
      Volume: 2200, OI: 3500 (Good liquidity)
      IV: 32% (Moderate volatility)
```

## 🛠️ Technical Details

### Data Sources

- **Stock Prices**: yfinance real-time data
- **Options Data**: yfinance options chains
- **Risk-Free Rate**: 3-month Treasury yield (^IRX)
- **Implied Volatility**: From options market

### Black-Scholes Model

Uses the standard Black-Scholes formula with:

- European-style options
- No dividends (can be modified)
- Constant volatility
- Risk-free rate

### Database Schema

```sql
CREATE TABLE yfinance_options (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR,
    contractSymbol VARCHAR,
    strike FLOAT,
    lastPrice FLOAT,
    bid FLOAT,
    ask FLOAT,
    impliedVolatility FLOAT,
    volume INTEGER,
    openInterest INTEGER,
    option_type VARCHAR,
    expiration_date DATETIME,
    current_stock_price FLOAT,
    risk_free_rate FLOAT,
    time_to_expiry FLOAT,
    black_scholes_price FLOAT,
    variance_percentage FLOAT,
    timestamp DATETIME
);
```

## 🚨 Important Disclaimers

### Educational Purpose Only

This tool is for educational and research purposes only. It does not constitute investment advice.

### No Guarantees

- Past performance doesn't guarantee future results
- High variance doesn't guarantee profitable trades
- Always do your own research and due diligence

### Risk Warnings

- Options trading involves substantial risk
- You can lose more than your initial investment
- Consider consulting a financial advisor

## 🔍 Troubleshooting

### Rate Limiting Issues

If you encounter "Too Many Requests" errors:

1. Wait a few minutes between requests
2. Reduce the number of symbols analyzed
3. Use the `--show-only` flag to view existing data

### Data Quality Issues

- Verify stock symbols are correct
- Check market hours (data may be stale outside trading hours)
- Ensure internet connection is stable

### Database Issues

- Run `--init-db` to recreate tables
- Check file permissions for SQLite database
- Ensure sufficient disk space

## 📚 Advanced Usage

### Custom Analysis

```python
from option_data_fetcher import OptionDataFetcher

# Create custom fetcher
fetcher = OptionDataFetcher(risk_free_rate=0.04)

# Analyze specific symbols
results = fetcher.fetch_and_store_options(['AAPL', 'TSLA'], variance_threshold=30.0)

# Get high variance options
high_variance = fetcher.get_high_variance_options(threshold=25.0)

# Get summary statistics
summary = fetcher.get_analysis_summary()
```

### Integration with Other Tools

- Export to Excel for further analysis
- Connect to trading platforms via API
- Build custom dashboards
- Set up automated alerts

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review the demo script: `python demo_option_analysis.py`
3. Test with mock data first
4. Check the main README.md for general project information

---

**Remember**: This is a powerful tool for identifying potential opportunities, but always combine it with proper risk management and thorough analysis before making any trading decisions.
