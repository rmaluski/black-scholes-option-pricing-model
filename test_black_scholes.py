import math
import pytest
from black_scholes import black_scholes_price

def test_call_basic():
    price = black_scholes_price(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
    assert 10 < price < 11  # Known value: ~10.45

def test_put_basic():
    price = black_scholes_price(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="put")
    assert 5 < price < 6    # Known value: ~5.57

def test_zero_volatility_call():
    price = black_scholes_price(S=100, K=90, T=1, r=0.05, sigma=0.0, option_type="call")
    expected = math.exp(-0.05 * 1) * max(0, 100 - 90)
    assert abs(price - expected) < 1e-8

def test_zero_volatility_put():
    price = black_scholes_price(S=80, K=100, T=1, r=0.05, sigma=0.0, option_type="put")
    expected = math.exp(-0.05 * 1) * max(0, 100 - 80)
    assert abs(price - expected) < 1e-8

def test_zero_time_call():
    price = black_scholes_price(S=120, K=100, T=0, r=0.05, sigma=0.2, option_type="call")
    assert price == 20

def test_zero_time_put():
    price = black_scholes_price(S=80, K=100, T=0, r=0.05, sigma=0.2, option_type="put")
    assert price == 20

def test_deep_in_the_money_call():
    price = black_scholes_price(S=200, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
    assert price > 95

def test_deep_out_of_the_money_call():
    price = black_scholes_price(S=50, K=100, T=1, r=0.05, sigma=0.2, option_type="call")
    assert price < 1

def test_negative_interest_rate():
    price = black_scholes_price(S=100, K=100, T=1, r=-0.01, sigma=0.2, option_type="call")
    assert price > 7 and price < 10 

def test_dividend_yield_call():
    price = black_scholes_price(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="call", q=0.03)
    assert 8.5 < price < 8.8  # Known value: ~8.65

def test_dividend_yield_put():
    price = black_scholes_price(S=100, K=100, T=1, r=0.05, sigma=0.2, option_type="put", q=0.03)
    assert 6.6 < price < 6.8  # Known value: ~6.73

def test_put_call_parity():
    S, K, T, r, sigma, q = 100, 100, 1, 0.05, 0.2, 0.03
    call = black_scholes_price(S, K, T, r, sigma, option_type="call", q=q)
    put = black_scholes_price(S, K, T, r, sigma, option_type="put", q=q)
    lhs = call - put
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert abs(lhs - rhs) < 1e-6 