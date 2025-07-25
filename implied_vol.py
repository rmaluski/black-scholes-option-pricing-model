import yfinance as yf
import numpy as np
from scipy.optimize import brentq
from black_scholes import black_scholes_price
import matplotlib.pyplot as plt

def implied_vol(S, K, T, r, market_price, option_type):
    def objective(sigma):
        return black_scholes_price(S, K, T, r, sigma, option_type) - market_price
    try:
        return brentq(objective, 1e-6, 5.0, maxiter=100)
    except Exception:
        return np.nan

def fetch_option_chain(ticker, expiry):
    stock = yf.Ticker(ticker)
    opt = stock.option_chain(expiry)
    return opt

def plot_iv_smile(ticker, expiry, r=0.01, option_type="call"):
    opt = fetch_option_chain(ticker, expiry)
    chain = opt.calls if option_type == "call" else opt.puts
    S = yf.Ticker(ticker).history(period="1d")['Close'][-1]
    T = (np.datetime64(expiry) - np.datetime64('today')).astype(float) / 365
    strikes = chain['strike'].values
    market_prices = chain['lastPrice'].values
    ivs = [implied_vol(S, K, T, r, price, option_type) for K, price in zip(strikes, market_prices)]
    plt.figure()
    plt.plot(strikes, ivs, marker='o')
    plt.xlabel('Strike')
    plt.ylabel('Implied Volatility')
    plt.title(f'Implied Volatility Smile ({option_type.capitalize()})')
    plt.grid(True)
    plt.show()
    return strikes, ivs 