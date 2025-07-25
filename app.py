import streamlit as st
from black_scholes import black_scholes_price
import numpy as np
import matplotlib.pyplot as plt
from models import OptionInput, OptionOutput, SessionLocal, init_db
import json

init_db()

st.title("Black-Scholes Option Pricing Model")

st.sidebar.header("Input Parameters")
S = st.sidebar.number_input("Spot price (S)", min_value=0.0, value=100.0)
K = st.sidebar.number_input("Strike price (K)", min_value=0.0, value=100.0)
T = st.sidebar.number_input("Time to maturity (T, years)", min_value=0.0, value=1.0)
r = st.sidebar.number_input("Risk-free rate (r, decimal)", value=0.05)
sigma = st.sidebar.number_input("Volatility (sigma, decimal)", min_value=0.0, value=0.2)
option_type = st.sidebar.selectbox("Option type", ["call", "put"])
purchase_price = st.sidebar.number_input("Purchase price", min_value=0.0, value=10.0)

st.sidebar.header("Heatmap Ranges")
spot_min = st.sidebar.number_input("Spot min", min_value=1.0, value=80.0)
spot_max = st.sidebar.number_input("Spot max", min_value=1.0, value=120.0)
spot_steps = st.sidebar.slider("Spot steps", min_value=5, max_value=50, value=20)
vol_min = st.sidebar.number_input("Volatility min", min_value=0.01, value=0.1)
vol_max = st.sidebar.number_input("Volatility max", min_value=0.01, value=0.5)
vol_steps = st.sidebar.slider("Volatility steps", min_value=5, max_value=50, value=20)

if st.sidebar.button("Calculate"):
    price = black_scholes_price(S, K, T, r, sigma, option_type)
    st.subheader(f"{option_type.capitalize()} Option Price")
    st.table({"Price": [f"{price:.4f}"]})

    # Heatmap calculation
    spot_range = np.linspace(spot_min, spot_max, spot_steps)
    vol_range = np.linspace(vol_min, vol_max, vol_steps)
    price_grid = np.zeros((len(spot_range), len(vol_range)))
    pnl_grid = np.zeros_like(price_grid)
    for i, s in enumerate(spot_range):
        for j, v in enumerate(vol_range):
            p = black_scholes_price(s, K, T, r, v, option_type)
            price_grid[i, j] = p
            pnl_grid[i, j] = p - purchase_price

    # Store input and output in DB
    session = SessionLocal()
    input_row = OptionInput(
        S=S, K=K, T=T, r=r, sigma=sigma, option_type=option_type, purchase_price=purchase_price
    )
    session.add(input_row)
    session.commit()
    output_row = OptionOutput(
        input_id=input_row.id,
        price=price,
        pnl_grid=json.dumps(pnl_grid.tolist())
    )
    session.add(output_row)
    session.commit()
    session.close()

    # Option price heatmap
    fig1, ax1 = plt.subplots()
    c1 = ax1.imshow(price_grid, aspect='auto', origin='lower',
                   extent=[vol_min, vol_max, spot_min, spot_max],
                   cmap='viridis')
    ax1.set_xlabel('Volatility (sigma)')
    ax1.set_ylabel('Spot Price (S)')
    ax1.set_title(f'{option_type.capitalize()} Option Price Heatmap')
    fig1.colorbar(c1, ax=ax1, label='Option Price')
    st.pyplot(fig1)

    # P&L heatmap (green for profit, red for loss)
    fig2, ax2 = plt.subplots()
    c2 = ax2.imshow(pnl_grid, aspect='auto', origin='lower',
                   extent=[vol_min, vol_max, spot_min, spot_max],
                   cmap='RdYlGn')
    ax2.set_xlabel('Volatility (sigma)')
    ax2.set_ylabel('Spot Price (S)')
    ax2.set_title(f'{option_type.capitalize()} Option P&L Heatmap (vs. Purchase Price)')
    fig2.colorbar(c2, ax=ax2, label='P&L')
    st.pyplot(fig2) 