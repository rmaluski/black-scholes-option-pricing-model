import math
from typing import Literal

def _d1(S, K, T, r, sigma):
    return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

def _d2(S, K, T, r, sigma):
    return _d1(S, K, T, r, sigma) - sigma * math.sqrt(T)

def N(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def n(x):
    return math.exp(-0.5 * x ** 2) / math.sqrt(2 * math.pi)

def delta(S, K, T, r, sigma, option_type: Literal["call", "put"] = "call"):
    d1 = _d1(S, K, T, r, sigma)
    if option_type == "call":
        return N(d1)
    else:
        return N(d1) - 1

def gamma(S, K, T, r, sigma):
    d1 = _d1(S, K, T, r, sigma)
    return n(d1) / (S * sigma * math.sqrt(T))

def theta(S, K, T, r, sigma, option_type: Literal["call", "put"] = "call"):
    d1 = _d1(S, K, T, r, sigma)
    d2 = _d2(S, K, T, r, sigma)
    first = -S * n(d1) * sigma / (2 * math.sqrt(T))
    if option_type == "call":
        second = -r * K * math.exp(-r * T) * N(d2)
        return (first + second) / 365
    else:
        second = r * K * math.exp(-r * T) * N(-d2)
        return (first + second) / 365

def vega(S, K, T, r, sigma):
    d1 = _d1(S, K, T, r, sigma)
    return S * n(d1) * math.sqrt(T) / 100

def rho(S, K, T, r, sigma, option_type: Literal["call", "put"] = "call"):
    d2 = _d2(S, K, T, r, sigma)
    if option_type == "call":
        return K * T * math.exp(-r * T) * N(d2) / 100
    else:
        return -K * T * math.exp(-r * T) * N(-d2) / 100 