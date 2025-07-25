from fastapi import FastAPI
from pydantic import BaseModel
from black_scholes import black_scholes_price
from greeks import delta, gamma, theta, vega, rho

app = FastAPI()

class OptionRequest(BaseModel):
    S: float
    K: float
    T: float
    r: float
    sigma: float
    option_type: str = "call"
    q: float = 0.0

@app.post("/price")
def price(req: OptionRequest):
    price = black_scholes_price(
        S=req.S, K=req.K, T=req.T, r=req.r, sigma=req.sigma, option_type=req.option_type, q=req.q
    )
    return {"price": price}

@app.post("/greeks")
def greeks(req: OptionRequest):
    d = delta(req.S, req.K, req.T, req.r, req.sigma, req.option_type)
    g = gamma(req.S, req.K, req.T, req.r, req.sigma)
    t = theta(req.S, req.K, req.T, req.r, req.sigma, req.option_type)
    v = vega(req.S, req.K, req.T, req.r, req.sigma)
    r_ = rho(req.S, req.K, req.T, req.r, req.sigma, req.option_type)
    return {"delta": d, "gamma": g, "theta": t, "vega": v, "rho": r_} 