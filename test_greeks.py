import math
import pytest
from greeks import delta, gamma, theta, vega, rho

def test_delta_call():
    d = delta(100, 100, 1, 0.05, 0.2, 'call')
    assert 0.63 < d < 0.64

def test_delta_put():
    d = delta(100, 100, 1, 0.05, 0.2, 'put')
    assert -0.37 < d < -0.36

def test_gamma():
    g = gamma(100, 100, 1, 0.05, 0.2)
    assert 0.018 < g < 0.019

def test_theta_call():
    t = theta(100, 100, 1, 0.05, 0.2, 'call')
    assert -0.02 < t < -0.01

def test_theta_put():
    t = theta(100, 100, 1, 0.05, 0.2, 'put')
    assert -0.02 < t < -0.01

def test_vega():
    v = vega(100, 100, 1, 0.05, 0.2)
    assert 0.37 < v < 0.38

def test_rho_call():
    r_ = rho(100, 100, 1, 0.05, 0.2, 'call')
    assert 0.53 < r_ < 0.54

def test_rho_put():
    r_ = rho(100, 100, 1, 0.05, 0.2, 'put')
    assert -0.44 < r_ < -0.43

def test_greeks_zero_time():
    # At expiry, gamma/theta/vega/rho should be near zero, delta is 0 or 1
    assert delta(120, 100, 0, 0.05, 0.2, 'call') == 1
    assert delta(80, 100, 0, 0.05, 0.2, 'call') == 0
    assert gamma(100, 100, 0, 0.05, 0.2) == 0
    assert abs(theta(100, 100, 0, 0.05, 0.2, 'call')) < 1e-6
    assert abs(vega(100, 100, 0, 0.05, 0.2)) < 1e-6
    assert abs(rho(100, 100, 0, 0.05, 0.2, 'call')) < 1e-6 