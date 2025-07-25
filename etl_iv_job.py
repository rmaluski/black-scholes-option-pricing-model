import yfinance as yf
import numpy as np
from implied_vol import implied_vol
from historical_iv_models import OptionIVHistory, SessionLocal, init_iv_db
import datetime
import time

def fetch_and_store_iv(ticker, expiry, r=0.01, option_type="call"):
    stock = yf.Ticker(ticker)
    opt = stock.option_chain(expiry)
    chain = opt.calls if option_type == "call" else opt.puts
    S = yf.Ticker(ticker).history(period="1d")['Close'][-1]
    T = (np.datetime64(expiry) - np.datetime64('today')).astype(float) / 365
    strikes = chain['strike'].values
    market_prices = chain['lastPrice'].values
    session = SessionLocal()
    for K, price in zip(strikes, market_prices):
        iv = implied_vol(S, K, T, r, price, option_type)
        row = OptionIVHistory(
            ticker=ticker,
            expiry=expiry,
            strike=K,
            option_type=option_type,
            iv=iv,
            timestamp=datetime.datetime.utcnow()
        )
        session.add(row)
    session.commit()
    session.close()

def nightly_etl():
    init_iv_db()
    tickers = ["AAPL", "MSFT", "GOOG"]
    expiry = "2024-12-20"  # Example expiry; in production, loop over available expiries
    for ticker in tickers:
        for option_type in ["call", "put"]:
            fetch_and_store_iv(ticker, expiry, r=0.01, option_type=option_type)

if __name__ == "__main__":
    nightly_etl() 