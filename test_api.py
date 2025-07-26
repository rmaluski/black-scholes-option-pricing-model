import requests
import pytest

API_URL = "http://localhost:8000"

@pytest.mark.parametrize("option_type,expected", [
    ("call", (10, 11)),
    ("put", (5, 6)),
])
def test_api_price(option_type, expected):
    payload = {"S": 100, "K": 100, "T": 1, "r": 0.05, "sigma": 0.2, "option_type": option_type, "q": 0.0}
    resp = requests.post(f"{API_URL}/price", json=payload)
    assert resp.status_code == 200
    price = resp.json()["price"]
    assert expected[0] < price < expected[1]

def test_api_greeks():
    payload = {"S": 100, "K": 100, "T": 1, "r": 0.05, "sigma": 0.2, "option_type": "call", "q": 0.0}
    resp = requests.post(f"{API_URL}/greeks", json=payload)
    assert resp.status_code == 200
    greeks = resp.json()
    assert 0.63 < greeks["delta"] < 0.64
    assert 0.018 < greeks["gamma"] < 0.019
    assert -0.02 < greeks["theta"] < -0.01
    assert 0.37 < greeks["vega"] < 0.38
    assert 0.53 < greeks["rho"] < 0.54 