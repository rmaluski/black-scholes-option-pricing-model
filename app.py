import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
from models import OptionInput, OptionOutput, SessionLocal, init_db
import json
from greeks import delta, gamma, theta, vega, rho
from mpl_toolkits.mplot3d import Axes3D
from implied_vol import plot_iv_smile
from model_comparison import benchmark_models
import pandas as pd
from black_scholes import black_scholes_price

# --- UX polish: set page config ---
st.set_page_config(
    page_title="Black-Scholes Option Pricing Model",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/rmaluski/black-scholes-option-pricing-model',
        'About': "A comprehensive Python project for option pricing, analytics, and visualization."
    }
)

# --- Theme toggle ---
theme = st.sidebar.radio("Theme", ["Light", "Dark"], index=0)
if theme == "Dark":
    st.markdown(
        """
        <style>
        body, .stApp { background-color: #222 !important; color: #eee !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

init_db()

st.title("Black-Scholes Option Pricing Model")

API_URL = "http://localhost:8000"

tabs = st.tabs(["Pricer", "Greeks Dashboard", "Implied Volatility Smile", "Model Comparison"])

with tabs[0]:
    st.sidebar.header("Input Parameters")
    # --- Animated sliders ---
    spot_min, spot_max = 80.0, 120.0
    vol_min, vol_max = 0.1, 0.5
    time_min, time_max = 0.01, 2.0
    spot = st.sidebar.slider("Spot price (S)", min_value=spot_min, max_value=spot_max, value=100.0, step=0.5)
    vol = st.sidebar.slider("Volatility (sigma, decimal)", min_value=vol_min, max_value=vol_max, value=0.2, step=0.01)
    time = st.sidebar.slider("Time to maturity (T, years)", min_value=time_min, max_value=time_max, value=1.0, step=0.01)
    play = st.sidebar.checkbox("Animate spot/vol/time")
    if play:
        import time as pytime
        for s in np.linspace(spot_min, spot_max, 20):
            for v in np.linspace(vol_min, vol_max, 10):
                for t in np.linspace(time_min, time_max, 5):
                    st.sidebar.write(f"S={s:.2f}, sigma={v:.2f}, T={t:.2f}")
                    payload = {"S": s, "K": 100, "T": t, "r": 0.05, "sigma": v, "option_type": "call", "q": 0.0}
                    resp = requests.post(f"{API_URL}/price", json=payload)
                    price = resp.json()["price"]
                    st.metric(label="Call Price", value=f"{price:.2f}")
                    pytime.sleep(0.1)
    K = st.sidebar.number_input("Strike price (K)", min_value=0.0, value=100.0)
    r = st.sidebar.number_input("Risk-free rate (r, decimal)", value=0.05)
    option_type = st.sidebar.selectbox("Option type", ["call", "put"])
    purchase_price = st.sidebar.number_input("Purchase price", min_value=0.0, value=10.0)

    st.sidebar.header("Heatmap Ranges")
    spot_steps = st.sidebar.slider("Spot steps", min_value=5, max_value=50, value=20)
    vol_steps = st.sidebar.slider("Volatility steps", min_value=5, max_value=50, value=20)

    if st.sidebar.button("Calculate") and not play:
        payload = {
            "S": spot, "K": K, "T": time, "r": r, "sigma": vol, "option_type": option_type, "q": 0.0
        }
        resp = requests.post(f"{API_URL}/price", json=payload)
        price = resp.json()["price"]
        st.subheader(f"{option_type.capitalize()} Option Price")
        st.table({"Price": [f"{price:.4f}"]})

        # Heatmap calculation
        spot_range = np.linspace(spot_min, spot_max, spot_steps)
        vol_range = np.linspace(vol_min, vol_max, vol_steps)
        price_grid = np.zeros((len(spot_range), len(vol_range)))
        pnl_grid = np.zeros_like(price_grid)
        for i, s in enumerate(spot_range):
            for j, v in enumerate(vol_range):
                p = black_scholes_price(s, K, time, r, v, option_type)
                price_grid[i, j] = p
                pnl_grid[i, j] = p - purchase_price

        # Store input and output in DB
        session = SessionLocal()
        input_row = OptionInput(
            S=spot, K=K, T=time, r=r, sigma=vol, option_type=option_type, purchase_price=purchase_price
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

with tabs[1]:
    st.header("Greeks Dashboard")
    st.write("Line plots and 3D surface for Greeks.")
    S_range = np.linspace(spot_min, spot_max, spot_steps)
    sigma_range = np.linspace(vol_min, vol_max, vol_steps)
    # Line plots for a fixed sigma
    st.subheader("Line Plots (varying Spot, fixed Volatility)")
    delta_vals = []
    gamma_vals = []
    theta_vals = []
    vega_vals = []
    rho_vals = []
    for s in S_range:
        payload = {"S": s, "K": K, "T": time, "r": r, "sigma": vol, "option_type": option_type, "q": 0.0}
        resp = requests.post(f"{API_URL}/greeks", json=payload)
        greeks = resp.json()
        delta_vals.append(greeks["delta"])
        gamma_vals.append(greeks["gamma"])
        theta_vals.append(greeks["theta"])
        vega_vals.append(greeks["vega"])
        rho_vals.append(greeks["rho"])
    fig, ax = plt.subplots()
    ax.plot(S_range, delta_vals, label="Delta")
    ax.plot(S_range, gamma_vals, label="Gamma")
    ax.plot(S_range, theta_vals, label="Theta")
    ax.plot(S_range, vega_vals, label="Vega")
    ax.plot(S_range, rho_vals, label="Rho")
    ax.set_xlabel("Spot Price (S)")
    ax.set_ylabel("Greek Value")
    ax.set_title("Greeks vs Spot Price (fixed Volatility)")
    ax.legend()
    st.pyplot(fig)

    # 3D surface for Delta (Spot x Vol)
    st.subheader("3D Surface: Delta (Spot × Volatility)")
    S_grid, sigma_grid = np.meshgrid(S_range, sigma_range)
    delta_grid = np.zeros_like(S_grid)
    for i in range(S_grid.shape[0]):
        for j in range(S_grid.shape[1]):
            delta_grid[i, j] = delta(S_grid[i, j], K, time, r, sigma_grid[i, j], option_type)
    fig3d = plt.figure()
    ax3d = fig3d.add_subplot(111, projection='3d')
    ax3d.plot_surface(S_grid, sigma_grid, delta_grid, cmap='viridis')
    ax3d.set_xlabel('Spot Price (S)')
    ax3d.set_ylabel('Volatility (sigma)')
    ax3d.set_zlabel('Delta')
    ax3d.set_title('Delta Surface')
    st.pyplot(fig3d)

with tabs[2]:
    st.header("Implied Volatility Smile")
    st.write("Fetch option chain from Yahoo Finance and plot IV smile.")
    ticker = st.text_input("Ticker", value="AAPL")
    expiry = st.text_input("Expiry (YYYY-MM-DD)", value="2024-12-20")
    option_type_iv = st.selectbox("Option type", ["call", "put"], key="iv_type")
    r_iv = st.number_input("Risk-free rate (r, decimal)", value=0.01, key="iv_r")
    if st.button("Plot IV Smile"):
        with st.spinner("Fetching data and calculating implied vols..."):
            try:
                strikes, ivs = plot_iv_smile(ticker, expiry, r=r_iv, option_type=option_type_iv)
                st.line_chart({"Strike": strikes, "Implied Vol": ivs})
            except Exception as e:
                st.error(f"Error: {e}")

with tabs[3]:
    st.header("Model Comparison: Black-Scholes, Binomial Tree, Monte Carlo")
    st.write("Benchmark accuracy and runtime for all three engines.")
    S_cmp = st.number_input("Spot price (S)", min_value=0.0, value=100.0, key="cmp_S")
    K_cmp = st.number_input("Strike price (K)", min_value=0.0, value=100.0, key="cmp_K")
    T_cmp = st.number_input("Time to maturity (T, years)", min_value=0.0, value=1.0, key="cmp_T")
    r_cmp = st.number_input("Risk-free rate (r, decimal)", value=0.05, key="cmp_r")
    sigma_cmp = st.number_input("Volatility (sigma, decimal)", min_value=0.0, value=0.2, key="cmp_sigma")
    option_type_cmp = st.selectbox("Option type", ["call", "put"], key="cmp_type")
    if st.button("Run Model Comparison"):
        results = benchmark_models(S_cmp, K_cmp, T_cmp, r_cmp, sigma_cmp, option_type_cmp)
        df = pd.DataFrame(results).T
        df["abs_error_vs_BS"] = abs(df["price"] - df.loc["Black-Scholes", "price"])
        st.dataframe(df.style.highlight_min(subset=["abs_error_vs_BS", "time"], color="lightgreen")) 