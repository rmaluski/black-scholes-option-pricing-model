import numpy as np
import time
from black_scholes import black_scholes_price

def binomial_tree_price(S, K, T, r, sigma, option_type="call", steps=1000):
    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1 / u
    p = (np.exp(r * dt) - d) / (u - d)
    disc = np.exp(-r * dt)
    # Terminal payoffs
    ST = S * u ** np.arange(steps, -1, -1) * d ** np.arange(0, steps + 1)
    if option_type == "call":
        values = np.maximum(ST - K, 0)
    else:
        values = np.maximum(K - ST, 0)
    # Backward induction
    for _ in range(steps):
        values = disc * (p * values[:-1] + (1 - p) * values[1:])
    return values[0]

def monte_carlo_price(S, K, T, r, sigma, option_type="call", n_paths=100000):
    np.random.seed(42)
    Z = np.random.standard_normal(n_paths)
    ST = S * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)
    if option_type == "call":
        payoffs = np.maximum(ST - K, 0)
    else:
        payoffs = np.maximum(K - ST, 0)
    price = np.exp(-r * T) * np.mean(payoffs)
    return price

def benchmark_models(S, K, T, r, sigma, option_type="call"):
    results = {}
    # Black-Scholes
    t0 = time.time()
    bs = black_scholes_price(S, K, T, r, sigma, option_type)
    t1 = time.time()
    results["Black-Scholes"] = {"price": bs, "time": t1 - t0}
    # Binomial Tree
    t0 = time.time()
    bt = binomial_tree_price(S, K, T, r, sigma, option_type)
    t1 = time.time()
    results["Binomial Tree"] = {"price": bt, "time": t1 - t0}
    # Monte Carlo
    t0 = time.time()
    mc = monte_carlo_price(S, K, T, r, sigma, option_type)
    t1 = time.time()
    results["Monte Carlo"] = {"price": mc, "time": t1 - t0}
    return results 