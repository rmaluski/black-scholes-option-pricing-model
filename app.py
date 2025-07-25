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
import datetime

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
# Remove dark mode/theme toggle and custom CSS

init_db()

st.title("Black-Scholes Option Pricing Model")

# --- Animated sliders ---
spot_min, spot_max = 80.0, 120.0
vol_min, vol_max = 0.1, 0.5
time_min, time_max = 0.01, 2.0

tabs = st.tabs(["Pricer", "Greeks Dashboard", "Implied Volatility Smile", "Model Comparison"])

with tabs[0]:
    st.sidebar.header("Input Parameters")
    # Replace sliders with number_input text boxes for direct value entry
    spot = st.sidebar.number_input("Spot price (S)", min_value=spot_min, max_value=spot_max, value=100.0, step=0.5)
    vol = st.sidebar.number_input("Volatility (sigma, decimal)", min_value=vol_min, max_value=vol_max, value=0.2, step=0.01)
    # Replace T input with expiration date picker
    import datetime
    today = datetime.date.today()
    default_expiry = today + datetime.timedelta(days=30)
    expiry_date = st.sidebar.date_input("Expiration date", value=default_expiry, min_value=today)
    T = (expiry_date - today).days / 365.0
    play = st.sidebar.checkbox("Animate spot/vol/time")
    if play:
        import time as pytime
        for s in np.linspace(spot_min, spot_max, 20):
            for v in np.linspace(vol_min, vol_max, 10):
                for t in np.linspace(time_min, time_max, 5):
                    st.sidebar.write(f"S={s:.2f}, sigma={v:.2f}, T={t:.2f}")
                    payload = {"S": s, "K": 100, "T": t, "r": 0.05, "sigma": v, "option_type": "call", "q": 0.0}
                    price = black_scholes_price(**payload)
                    st.metric(label="Call Price", value=f"{price:.2f}")
                    pytime.sleep(0.1)
    K = st.sidebar.number_input("Strike price (K)", min_value=0.0, value=100.0)
    r = st.sidebar.number_input("Risk-free rate (r, decimal)", value=0.05)
    # Remove option type input from sidebar
    # purchase_price = st.sidebar.number_input("Purchase price", min_value=0.0, value=10.0)

    # Remove Spot steps and Volatility steps sliders from sidebar
    # spot_steps = st.sidebar.slider("Spot steps", min_value=5, max_value=50, value=20)
    # vol_steps = st.sidebar.slider("Volatility steps", min_value=5, max_value=50, value=20)

    # Add a session state to store last calculated prices
    if 'last_call_price' not in st.session_state:
        st.session_state['last_call_price'] = None
    if 'last_put_price' not in st.session_state:
        st.session_state['last_put_price'] = None

    # Update Latest Option Prices section to show two colored boxes
    show_call_price = st.session_state.get('last_call_price')
    show_put_price = st.session_state.get('last_put_price')

    if st.sidebar.button("Calculate") and not play:
        # Use T in all pricing calculations (replace 'time' with 'T')
        payload = {
            "S": spot, "K": K, "T": T, "r": r, "sigma": vol, "q": 0.0
        }
        call_price = black_scholes_price(**payload, option_type="call")
        put_price = black_scholes_price(**payload, option_type="put")
        st.session_state['last_call_price'] = call_price
        st.session_state['last_put_price'] = put_price
        show_call_price = call_price
        show_put_price = put_price

    call_display = f"{show_call_price:.4f}" if show_call_price is not None else "--"
    put_display = f"{show_put_price:.4f}" if show_put_price is not None else "--"

    st.subheader("Latest Option Prices")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='background-color:#2ecc40;padding:20px;border-radius:10px;text-align:center;'><span style='color:white;font-size:24px;font-weight:bold;'>Call Value</span><br><span style='color:white;font-size:32px;font-weight:bold;'>{call_display}</span></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='background-color:#e74c3c;padding:20px;border-radius:10px;text-align:center;'><span style='color:white;font-size:24px;font-weight:bold;'>Put Value</span><br><span style='color:white;font-size:32px;font-weight:bold;'>{put_display}</span></div>", unsafe_allow_html=True)

    # Set heatmap grid steps to a fixed value
    grid_steps = 12
    spot_range = np.linspace(spot_min, spot_max, grid_steps)
    vol_range = np.linspace(vol_min, vol_max, grid_steps)
    call_price_grid = np.zeros((len(vol_range), len(spot_range)))
    put_price_grid = np.zeros_like(call_price_grid)
    # call_pnl_grid = np.zeros_like(call_price_grid)
    # put_pnl_grid = np.zeros_like(call_price_grid)
    for i, v in enumerate(vol_range):
        for j, s in enumerate(spot_range):
            call_p = black_scholes_price(s, K, T, r, v, option_type="call", q=0.0)
            put_p = black_scholes_price(s, K, T, r, v, option_type="put", q=0.0)
            call_price_grid[i, j] = call_p
            put_price_grid[i, j] = put_p
            # call_pnl_grid[i, j] = call_p - purchase_price
            # put_pnl_grid[i, j] = put_p - purchase_price

    # Call price heatmap with value annotations (index-based centering)
    fig1, ax1 = plt.subplots()
    c1 = ax1.imshow(call_price_grid, aspect='auto', origin='lower', cmap='viridis')
    ax1.set_xlabel('Spot Price (S)')
    ax1.set_ylabel('Volatility (sigma)')
    ax1.set_title('Call Price Heatmap')
    fig1.colorbar(c1, ax=ax1, label='Call Price')
    # Set ticks to match actual values
    ax1.set_xticks(np.arange(len(spot_range)))
    ax1.set_yticks(np.arange(len(vol_range)))
    ax1.set_xticklabels([f"{s:.2f}" for s in spot_range], rotation=45, ha="right")
    ax1.set_yticklabels([f"{v:.2f}" for v in vol_range])
    # Center numbers in each box
    for i in range(call_price_grid.shape[0]):
        for j in range(call_price_grid.shape[1]):
            ax1.text(j, i, f"{call_price_grid[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig1.tight_layout()
    st.pyplot(fig1)

    # Put price heatmap with value annotations (index-based centering)
    fig2, ax2 = plt.subplots()
    c2 = ax2.imshow(put_price_grid, aspect='auto', origin='lower', cmap='viridis')
    ax2.set_xlabel('Spot Price (S)')
    ax2.set_ylabel('Volatility (sigma)')
    ax2.set_title('Put Price Heatmap')
    fig2.colorbar(c2, ax=ax2, label='Put Price')
    ax2.set_xticks(np.arange(len(spot_range)))
    ax2.set_yticks(np.arange(len(vol_range)))
    ax2.set_xticklabels([f"{s:.2f}" for s in spot_range], rotation=45, ha="right")
    ax2.set_yticklabels([f"{v:.2f}" for v in vol_range])
    for i in range(put_price_grid.shape[0]):
        for j in range(put_price_grid.shape[1]):
            ax2.text(j, i, f"{put_price_grid[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig2.tight_layout()
    st.pyplot(fig2)

    # Store input and output in DB (store call price as before)
    session = SessionLocal()
    input_row = OptionInput(
        S=spot, K=K, T=T, r=r, sigma=vol, option_type="call"
    )
    session.add(input_row)
    session.commit()
    output_row = OptionOutput(
        input_id=input_row.id,
        price=st.session_state['last_call_price'],  # Use session state value
        pnl_grid="[]"  # No P&L grid
    )
    session.add(output_row)
    session.commit()
    session.close()


with tabs[1]:
    st.header("Greeks Dashboard")
    st.write("Line plots and 3D surface for Greeks.")
    S_range = np.linspace(spot_min, spot_max, grid_steps)
    sigma_range = np.linspace(vol_min, vol_max, grid_steps)
    # Line plots for a fixed sigma
    st.subheader("Line Plots (varying Spot, fixed Volatility)")
    delta_vals = []
    gamma_vals = []
    theta_vals = []
    vega_vals = []
    rho_vals = []
    for s in S_range:
        payload = {"S": s, "K": K, "T": T, "r": r, "sigma": vol, "option_type": "call", "q": 0.0}
        delta_args = {k: payload[k] for k in ["S", "K", "T", "r", "sigma", "option_type"]}
        base_args = {k: payload[k] for k in ["S", "K", "T", "r", "sigma"]}
        delta_vals.append(delta(**delta_args))
        gamma_vals.append(gamma(**base_args))
        theta_vals.append(theta(**base_args))
        vega_vals.append(vega(**base_args))
        rho_vals.append(rho(**base_args))
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
            delta_grid[i, j] = delta(S_grid[i, j], K, T, r, sigma_grid[i, j], "call")
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
    # Calculate the 3rd Friday of next month
    today = datetime.date.today()
    year = today.year + (1 if today.month == 12 else 0)
    month = today.month + 1 if today.month < 12 else 1
    # Find all Fridays in the next month
    first_of_month = datetime.date(year, month, 1)
    fridays = [first_of_month + datetime.timedelta(days=(4 - first_of_month.weekday() + 7 * i) % 7 + 7 * i)
               for i in range(5)]
    fridays = [d for d in fridays if d.month == month]
    third_friday = fridays[2] if len(fridays) >= 3 else fridays[-1]
    expiry = st.text_input("Expiry (YYYY-MM-DD)", value=third_friday.strftime("%Y-%m-%d"))
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