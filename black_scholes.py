import math
from typing import Literal

def black_scholes_price(
    S: float,  # Spot price
    K: float,  # Strike price
    T: float,  # Time to maturity (in years)
    r: float,  # Risk-free interest rate (annualized, decimal)
    sigma: float,  # Volatility (annualized, decimal)
    option_type: Literal["call", "put"] = "call",
    q: float = 0.0  # Continuous dividend yield (annualized, decimal)
) -> float:
    """
    Calculate the Black-Scholes price for a European call or put option, with optional continuous dividend yield.

    Parameters:
        S (float): Spot price of the underlying asset
        K (float): Strike price
        T (float): Time to maturity in years
        r (float): Risk-free interest rate (annualized, decimal)
        sigma (float): Volatility of the underlying asset (annualized, decimal)
        option_type (str): 'call' or 'put'
        q (float): Continuous dividend yield (annualized, decimal, default 0)

    Returns:
        float: Option price
    """
    if T <= 0:
        # Option has expired
        if option_type == "call":
            return max(0.0, S - K)
        else:
            return max(0.0, K - S)
    if sigma <= 0:
        # No volatility: option is worth intrinsic value discounted
        if option_type == "call":
            return math.exp(-r * T) * max(0.0, S - K)
        else:
            return math.exp(-r * T) * max(0.0, K - S)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    if option_type == "call":
        return S * math.exp(-q * T) * N(d1) - K * math.exp(-r * T) * N(d2)
    else:
        return K * math.exp(-r * T) * N(-d2) - S * math.exp(-q * T) * N(-d1) 