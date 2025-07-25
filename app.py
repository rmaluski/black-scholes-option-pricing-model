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
import yfinance as yf

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
vol_min, vol_max = 0.1, 0.5
time_min, time_max = 0.01, 2.0

tabs = st.tabs(["Pricer", "Greeks Dashboard", "Implied Volatility Smile", "Model Comparison"])

with tabs[0]:
    st.sidebar.header("Input Parameters")
    # Replace sliders with number_input text boxes for direct value entry
    import yfinance as yf
    # Fetch the latest 10-year Treasury yield
    def get_10yr_treasury_yield():
        tnx = yf.Ticker("^TNX")
        data = tnx.history(period="1d")
        if not data.empty:
            return data["Close"].iloc[-1] / 100  # Convert percent to decimal
        else:
            return 0.04  # fallback default
    default_rf = get_10yr_treasury_yield()

    # Fetch the latest VIX value
    def get_vix():
        vix = yf.Ticker("^VIX")
        data = vix.history(period="1d")
        if not data.empty:
            return data["Close"].iloc[-1] / 100  # Convert percent to decimal
        else:
            return 0.20  # fallback default
    default_vix = get_vix()

    # Add ticker input to sidebar
    ticker_str = st.sidebar.text_input("Ticker Symbol", value="AAPL", help="Enter the stock ticker symbol (e.g., AAPL, MSFT, SPY)")

    # Fetch current stock price from yfinance
    def get_current_price(ticker):
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period="1d")
            if not data.empty:
                return data["Close"].iloc[-1]
            else:
                return 100.0  # fallback default
        except Exception:
            return 100.0  # fallback default

    # Get current price for the ticker
    current_price = get_current_price(ticker_str)
    st.sidebar.markdown(f"**Current {ticker_str} Price:** ${current_price:.2f}")

    spot = st.sidebar.number_input("Spot price (S)", min_value=0.01, value=current_price, step=0.01, format="%.2f")
    
    # Display VIX value above volatility input
    st.sidebar.markdown(f"**VIX (30d Implied Vol):** {default_vix:.4%}")
    vol = st.sidebar.number_input("Volatility (sigma, decimal)", min_value=vol_min, max_value=vol_max, value=default_vix, step=0.000001, format="%.6f")
    
    # Display 10Y Treasury yield above risk-free rate input
    st.sidebar.markdown(f"**10Y Treasury Yield:** {default_rf:.4%}")
    r = st.sidebar.number_input("Risk-free rate (r, decimal)", value=default_rf, format="%.6f")
    st.sidebar.caption("If VIX=14.93, enter 0.1493 for volatility. VIX is a 30-day forward-looking implied volatility for the S&P 500.")
    # Set default expiry to the 3rd Friday of next month
    today = datetime.date.today()
    if today.month == 12:
        year = today.year + 1
        month = 1
    else:
        year = today.year
        month = today.month + 1
    first_of_month = datetime.date(year, month, 1)
    fridays = []
    for i in range(31):
        day = first_of_month + datetime.timedelta(days=i)
        if day.month != month:
            break
        if day.weekday() == 4:
            fridays.append(day)
    if len(fridays) >= 3:
        third_friday = fridays[2]
    else:
        third_friday = fridays[-1]
    expiry_date = st.sidebar.date_input("Expiration date", value=third_friday, min_value=today)
    T = (expiry_date - today).days / 365.0
    K = st.sidebar.number_input("Strike price (K)", min_value=0.0, value=100.0)
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

    # On Calculate, fetch market call/put prices from yfinance for comparison
    show_call_price = st.session_state.get('last_call_price')
    show_put_price = st.session_state.get('last_put_price')
    show_market_call = None
    show_market_put = None

    if st.sidebar.button("Calculate"):
        payload = {
            "S": spot, "K": K, "T": T, "r": r, "sigma": vol, "q": 0.0
        }
        call_price = black_scholes_price(**payload, option_type="call")
        put_price = black_scholes_price(**payload, option_type="put")
        st.session_state['last_call_price'] = call_price
        st.session_state['last_put_price'] = put_price
        show_call_price = call_price
        show_put_price = put_price

        # Fetch market prices from yfinance
        try:
            yf_ticker = yf.Ticker(ticker_str)
            opt_chain = yf_ticker.option_chain(expiry_date.strftime("%Y-%m-%d"))
            calls = opt_chain.calls
            puts = opt_chain.puts
            # Find closest strike
            call_row = calls.loc[(calls['strike'] - K).abs().idxmin()] if not calls.empty else None
            put_row = puts.loc[(puts['strike'] - K).abs().idxmin()] if not puts.empty else None
            show_market_call = call_row['lastPrice'] if call_row is not None else None
            show_market_put = put_row['lastPrice'] if put_row is not None else None
        except Exception:
            show_market_call = None
            show_market_put = None

    call_display = f"{show_call_price:.4f}" if show_call_price is not None else "--"
    put_display = f"{show_put_price:.4f}" if show_put_price is not None else "--"
    call_market_display = f"{show_market_call:.4f}" if show_market_call is not None else "--"
    put_market_display = f"{show_market_put:.4f}" if show_market_put is not None else "--"

    st.subheader("Latest Option Prices")
    col1, col2 = st.columns(2)
    with col1:
        # Call Price (market) above Call Value (Black-Scholes)
        st.markdown(f"<div style='background-color:#2980b9;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_market_display}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color:#2ecc40;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Value (Black-Scholes)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_display}</span></div>", unsafe_allow_html=True)
    with col2:
        # Put Price (market) above Put Value (Black-Scholes)
        st.markdown(f"<div style='background-color:#c0392b;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_market_display}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color:#e74c3c;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Value (Black-Scholes)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_display}</span></div>", unsafe_allow_html=True)

    # Set heatmap grid steps to a fixed value
    grid_steps = 12
    # Use dynamic range based on current spot price for heatmap
    spot_range = np.linspace(spot * 0.8, spot * 1.2, grid_steps)
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

    # Responsive heatmap layout based on screen size
    st.subheader("Option Price Heatmaps")
    
    # Create heatmaps with larger size for better visibility
    fig1, ax1 = plt.subplots(figsize=(8, 6))
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
            ax1.text(j, i, f"{call_price_grid[i, j]:.2f}", ha="center", va="center", color="white", fontsize=10)
    fig1.tight_layout()

    fig2, ax2 = plt.subplots(figsize=(8, 6))
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
            ax2.text(j, i, f"{put_price_grid[i, j]:.2f}", ha="center", va="center", color="white", fontsize=10)
    fig2.tight_layout()

    # Responsive layout: Use CSS to detect screen size and adjust layout
    st.markdown("""
    <style>
    @media (min-width: 1200px) {
        .heatmap-container {
            display: flex;
            gap: 20px;
        }
        .heatmap-item {
            flex: 1;
        }
    }
    @media (max-width: 1199px) {
        .heatmap-container {
            display: block;
        }
        .heatmap-item {
            margin-bottom: 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create responsive container
    st.markdown('<div class="heatmap-container">', unsafe_allow_html=True)
    
    # First heatmap
    st.markdown('<div class="heatmap-item">', unsafe_allow_html=True)
    st.pyplot(fig1, use_container_width=True, clear_figure=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Second heatmap
    st.markdown('<div class="heatmap-item">', unsafe_allow_html=True)
    st.pyplot(fig2, use_container_width=True, clear_figure=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Store input and output in DB (only if we have valid prices)
    if st.session_state.get('last_call_price') is not None:
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
    # Use dynamic range based on current spot price for Greeks dashboard
    S_range = np.linspace(spot * 0.8, spot * 1.2, grid_steps)
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