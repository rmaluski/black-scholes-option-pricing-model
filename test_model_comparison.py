import pytest
from model_comparison import binomial_tree_price, monte_carlo_price
from black_scholes import black_scholes_price

def test_binomial_tree_call():
    bs = black_scholes_price(100, 100, 1, 0.05, 0.2, 'call')
    bt = binomial_tree_price(100, 100, 1, 0.05, 0.2, 'call', steps=1000)
    assert abs(bs - bt) < 0.5

def test_binomial_tree_put():
    bs = black_scholes_price(100, 100, 1, 0.05, 0.2, 'put')
    bt = binomial_tree_price(100, 100, 1, 0.05, 0.2, 'put', steps=1000)
    assert abs(bs - bt) < 0.5

def test_monte_carlo_call():
    bs = black_scholes_price(100, 100, 1, 0.05, 0.2, 'call')
    mc = monte_carlo_price(100, 100, 1, 0.05, 0.2, 'call', n_paths=100000)
    assert abs(bs - mc) < 0.5

def test_monte_carlo_put():
    bs = black_scholes_price(100, 100, 1, 0.05, 0.2, 'put')
    mc = monte_carlo_price(100, 100, 1, 0.05, 0.2, 'put', n_paths=100000)
    assert abs(bs - mc) < 0.5 