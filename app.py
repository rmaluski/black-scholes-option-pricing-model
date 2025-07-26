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
from datetime import date, timedelta
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

st.title("Option Pricing Models")

# --- Animated sliders ---
vol_min, vol_max = 0.1, 0.5
time_min, time_max = 0.01, 2.0

tabs = st.tabs(["Black-Scholes", "Binomial Tree (Risk-Neutral)", "Binomial Tree (MC Probabilities)", "Monte Carlo", "Greeks Dashboard", "Implied Volatility Smile"])

# Shared sidebar for all pricing models
st.sidebar.header("Input Parameters")
# Fetch the latest 10-year Treasury yield
# (Original, simple version)
def get_10yr_treasury_yield():
    tnx = yf.Ticker("^TNX")
    data = tnx.history(period="1d")
    if data.empty:
        return 0.04  # fallback to 4%
    return data["Close"].iloc[-1] / 100

default_rf = get_10yr_treasury_yield()

# Fetch the latest VIX value
# (Original, simple version)
def get_vix():
    vix = yf.Ticker("^VIX")
    data = vix.history(period="1d")
    if data.empty:
        return 0.20  # fallback to 20%
    return data["Close"].iloc[-1] / 100

default_vix = get_vix()

# Add ticker input to sidebar
ticker_str = st.sidebar.text_input("Ticker Symbol", value="AAPL", help="Enter the stock ticker symbol (e.g., AAPL, MSFT, SPY)")

# Fetch current stock price from yfinance
# (Original, simple version)
def get_current_price(ticker):
    ticker_obj = yf.Ticker(ticker)
    data = ticker_obj.history(period="1d")
    if data.empty:
        return 100.0  # fallback to $100
    return data["Close"].iloc[-1]

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
today = date.today()
if today.month == 12:
    year = today.year + 1
    month = 1
else:
    year = today.year
    month = today.month + 1
first_of_month = date(year, month, 1)
fridays = []
for i in range(31):
    day = first_of_month + timedelta(days=i)
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

from black_scholes import black_scholes_price
from model_comparison import binomial_tree_price, monte_carlo_price

def get_option_market_price(ticker, expiry, strike, option_type):
    try:
        ticker_obj = yf.Ticker(ticker)
        opt_chain = ticker_obj.option_chain(str(expiry))
        df = opt_chain.calls if option_type == 'call' else opt_chain.puts
        row = df[df['strike'] == strike]
        if not row.empty:
            return float(row['lastPrice'].iloc[0])
    except Exception:
        pass
    return None

# --- Black-Scholes Tab ---
with tabs[0]:
    st.header("Black-Scholes Model")
    if st.button("Calculate Black-Scholes"):
        call_val = black_scholes_price(spot, K, T, r, vol, 'call')
        put_val = black_scholes_price(spot, K, T, r, vol, 'put')
        expiry_str = expiry_date.strftime('%Y-%m-%d')
        call_market = get_option_market_price(ticker_str, expiry_str, K, 'call')
        put_market = get_option_market_price(ticker_str, expiry_str, K, 'put')
        
        # Beautiful styled pricing display
        call_display = f"{call_val:.4f}"
        put_display = f"{put_val:.4f}"
        call_market_display = f"{call_market:.4f}" if call_market is not None else "N/A"
        put_market_display = f"{put_market:.4f}" if put_market is not None else "N/A"
        
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

        # --- Heatmap (Gridmap) Visualizations ---
        grid_steps = 12
        spot_range = np.linspace(spot * 0.8, spot * 1.2, grid_steps)
        vol_range = np.linspace(vol_min, vol_max, grid_steps)
        call_price_grid = np.zeros((len(vol_range), len(spot_range)))
        put_price_grid = np.zeros_like(call_price_grid)
        for i, v in enumerate(vol_range):
            for j, s in enumerate(spot_range):
                call_p = black_scholes_price(s, K, T, r, v, 'call')
                put_p = black_scholes_price(s, K, T, r, v, 'put')
                call_price_grid[i, j] = call_p
                put_price_grid[i, j] = put_p
        st.subheader("Option Price Heatmaps")
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        c1 = ax1.imshow(call_price_grid, aspect='auto', origin='lower', cmap='viridis')
        ax1.set_xlabel('Spot Price (S)')
        ax1.set_ylabel('Volatility (sigma)')
        ax1.set_title('Call Price Heatmap')
        fig1.colorbar(c1, ax=ax1, label='Call Price')
        ax1.set_xticks(np.arange(len(spot_range)))
        ax1.set_yticks(np.arange(len(vol_range)))
        ax1.set_xticklabels([f"{s:.2f}" for s in spot_range], rotation=45, ha="right")
        ax1.set_yticklabels([f"{v:.2f}" for v in vol_range])
        for i in range(call_price_grid.shape[0]):
            for j in range(call_price_grid.shape[1]):
                ax1.text(j, i, f"{call_price_grid[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
        fig1.tight_layout()
        fig2, ax2 = plt.subplots(figsize=(8, 5))
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
        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(fig1, use_container_width=True, clear_figure=True)
        with col2:
            st.pyplot(fig2, use_container_width=True, clear_figure=True)

# --- Binomial Tree Tab ---
with tabs[1]:
    st.header("Binomial Tree (Risk-Neutral)")
    n_steps = st.number_input("Number of Steps", min_value=1, max_value=500, value=100)
    if st.button("Calculate Binomial Tree"):
        call_val = binomial_tree_price(spot, K, T, r, vol, 'call', int(n_steps))
        put_val = binomial_tree_price(spot, K, T, r, vol, 'put', int(n_steps))
        expiry_str = expiry_date.strftime('%Y-%m-%d')
        call_market = get_option_market_price(ticker_str, expiry_str, K, 'call')
        put_market = get_option_market_price(ticker_str, expiry_str, K, 'put')
        
        # Beautiful styled pricing display
        call_display = f"{call_val:.4f}"
        put_display = f"{put_val:.4f}"
        call_market_display = f"{call_market:.4f}" if call_market is not None else "N/A"
        put_market_display = f"{put_market:.4f}" if put_market is not None else "N/A"
        
        st.subheader("Latest Option Prices")
        col1, col2 = st.columns(2)
        with col1:
            # Call Price (market) above Call Value (Binomial Tree)
            st.markdown(f"<div style='background-color:#2980b9;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_market_display}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#2ecc40;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Value (Binomial Tree)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_display}</span></div>", unsafe_allow_html=True)
        with col2:
            # Put Price (market) above Put Value (Binomial Tree)
            st.markdown(f"<div style='background-color:#c0392b;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_market_display}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#e74c3c;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Value (Binomial Tree)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_display}</span></div>", unsafe_allow_html=True)

        # --- Binomial Tree Structure Visualization ---
        st.subheader("Binomial Tree Structure")
        
        # Create a simplified tree visualization (showing first few levels)
        max_levels = min(6, int(n_steps))  # Show up to 6 levels for clarity
        dt = T / int(n_steps)
        u = np.exp(vol * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)  # Risk-neutral probability
        
        # Debug information
        st.subheader("Risk-Neutral Parameters")
        st.write(f"Risk-neutral probability (p): {p:.4f}")
        st.write(f"Up factor (u): {u:.4f}")
        st.write(f"Down factor (d): {d:.4f}")
        st.write(f"Time step (dt): {dt:.4f}")
        
        fig_tree, ax = plt.subplots(figsize=(14, 10))
        
        # Plot tree structure
        for level in range(max_levels + 1):
            for node in range(level + 1):
                # Calculate stock price at this node
                stock_price = spot * (u ** (level - node)) * (d ** node)
                
                # Calculate option value (simplified)
                if level == max_levels:  # Terminal nodes
                    call_value = max(stock_price - K, 0)
                    put_value = max(K - stock_price, 0)
                else:
                    # For non-terminal nodes, use a simplified calculation
                    call_value = call_val * (stock_price / spot)  # Approximation
                    put_value = put_val * (K / stock_price)  # Approximation
                
                # Position in tree
                x_pos = level
                y_pos = node - level/2
                
                # Plot node
                ax.plot(x_pos, y_pos, 'o', markersize=8, color='blue')
                
                # Add stock price label
                ax.text(x_pos, y_pos + 0.15, f'S: ${stock_price:.2f}', 
                       ha='center', va='bottom', fontsize=8)
                
                # Add option value label
                ax.text(x_pos, y_pos - 0.15, f'C: ${call_value:.2f}\nP: ${put_value:.2f}', 
                       ha='center', va='top', fontsize=7)
                
                # Connect to parent nodes and add probabilities
                if level > 0:
                    if node > 0:  # Connect to up-move parent
                        ax.plot([x_pos-1, x_pos], [y_pos-0.5, y_pos], 'k-', alpha=0.5)
                        # Add up probability
                        ax.text((x_pos-1 + x_pos)/2, (y_pos-0.5 + y_pos)/2 + 0.1, 
                               f'p={p:.3f}', ha='center', va='bottom', fontsize=7, 
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgreen', alpha=0.7))
                    if node < level:  # Connect to down-move parent
                        ax.plot([x_pos-1, x_pos], [y_pos+0.5, y_pos], 'k-', alpha=0.5)
                        # Add down probability
                        ax.text((x_pos-1 + x_pos)/2, (y_pos+0.5 + y_pos)/2 - 0.1, 
                               f'1-p={1-p:.3f}', ha='center', va='top', fontsize=7,
                               bbox=dict(boxstyle='round,pad=0.2', facecolor='lightcoral', alpha=0.7))
        
        ax.set_xlabel('Time Steps')
        ax.set_ylabel('Price Levels')
        ax.set_title(f'Binomial Tree Structure (First {max_levels} Levels)\nS₀=${spot:.2f}, K=${K:.2f}, σ={vol:.3f}, T={T:.3f}, p={p:.3f}')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.5, max_levels + 0.5)
        ax.set_ylim(-max_levels/2 - 0.5, max_levels/2 + 0.5)
        
        # Add legend
        ax.text(0.02, 0.98, 'S: Stock Price\nC: Call Value\nP: Put Value\np: Up Probability\n1-p: Down Probability', 
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        st.pyplot(fig_tree, use_container_width=True, clear_figure=True)

# --- Binomial Tree (MC Probabilities) Tab ---
with tabs[2]:
    st.header("Binomial Tree (MC Probabilities)")
    n_steps_mc = st.number_input("Number of Steps (MC)", min_value=1, max_value=500, value=100)
    if st.button("Calculate Binomial Tree (MC)"):
        # Fetch historical data for conditional probabilities
        try:
            ticker_obj = yf.Ticker(ticker_str)
            hist_data = ticker_obj.history(period="2y")  # Get more data for better conditional analysis
            
            # Function to calculate conditional probabilities at a given price level
            def calculate_conditional_probabilities(current_price, hist_data, price_tolerance=0.01):
                """Calculate up/down probabilities conditional on being near a specific price level"""
                # Find periods when stock was within price_tolerance% of current_price
                price_range = current_price * price_tolerance
                similar_price_periods = hist_data[
                    (hist_data['Close'] >= current_price - price_range) & 
                    (hist_data['Close'] <= current_price + price_range)
                ]
                
                if len(similar_price_periods) < 10:  # Need minimum data points
                    # Fallback to overall probabilities
                    returns = hist_data['Close'].pct_change().dropna()
                    up_moves = (returns > 0).sum()
                    total_moves = len(returns)
                    return up_moves / total_moves if total_moves > 0 else 0.5
                
                # Calculate returns for similar price periods
                similar_returns = similar_price_periods['Close'].pct_change().dropna()
                up_moves = (similar_returns > 0).sum()
                total_moves = len(similar_returns)
                
                return up_moves / total_moves if total_moves > 0 else 0.5
            
            # Function to run Monte Carlo simulations at a given price level
            def run_mc_simulations(current_price, hist_data, n_simulations=5000):
                """Run MC simulations to determine up/down probability from current price"""
                # Get conditional probability
                p_up = calculate_conditional_probabilities(current_price, hist_data)
                
                # Run MC simulations
                np.random.seed(42)  # For reproducibility
                simulations = np.random.random(n_simulations)
                up_count = (simulations < p_up).sum()
                
                return up_count / n_simulations
            
            # Custom MC-based binomial tree pricing function
            def mc_binomial_tree_price(S, K, T, r, hist_data, option_type="call", steps=100):
                """Calculate option price using MC-derived conditional probabilities"""
                dt = T / steps
                u = np.exp(empirical_vol * np.sqrt(dt))
                d = 1 / u
                
                # Terminal payoffs
                ST = S * u ** np.arange(steps, -1, -1) * d ** np.arange(0, steps + 1)
                if option_type == "call":
                    values = np.maximum(ST - K, 0)
                else:
                    values = np.maximum(K - ST, 0)
                
                # Backward induction with MC probabilities
                for step in range(steps):
                    new_values = np.zeros(len(values) - 1)
                    for i in range(len(values) - 1):
                        # Calculate current stock price at this node
                        current_price = S * (u ** (steps - step - 1 - i)) * (d ** i)
                        
                        # Get conditional probability for this price level
                        p_mc = calculate_conditional_probabilities(current_price, hist_data)
                        
                        # Use MC probability instead of risk-neutral probability
                        disc = np.exp(-r * dt)
                        new_values[i] = disc * (p_mc * values[i] + (1 - p_mc) * values[i + 1])
                    values = new_values
                
                return values[0]
            
            # Calculate empirical volatility from historical data
            returns = hist_data['Close'].pct_change().dropna()
            empirical_vol = returns.std() * np.sqrt(252)  # Annualized
            
            # Use MC-based pricing function
            call_val_mc = mc_binomial_tree_price(spot, K, T, r, hist_data, 'call', int(n_steps_mc))
            put_val_mc = mc_binomial_tree_price(spot, K, T, r, hist_data, 'put', int(n_steps_mc))
            
            # Debug information for MC approach
            st.subheader("MC Probabilities Parameters")
            st.write(f"Empirical volatility: {empirical_vol:.4f}")
            st.write(f"Overall up probability: {calculate_conditional_probabilities(spot, hist_data):.4f}")
            
            # Show a few sample conditional probabilities
            sample_prices = [spot * 0.95, spot, spot * 1.05]
            st.write("Sample conditional probabilities:")
            for price in sample_prices:
                cond_prob = calculate_conditional_probabilities(price, hist_data)
                st.write(f"  At ${price:.2f}: p = {cond_prob:.4f}")
            
            expiry_str = expiry_date.strftime('%Y-%m-%d')
            call_market = get_option_market_price(ticker_str, expiry_str, K, 'call')
            put_market = get_option_market_price(ticker_str, expiry_str, K, 'put')
            
            # Beautiful styled pricing display
            call_display = f"{call_val_mc:.4f}"
            put_display = f"{put_val_mc:.4f}"
            call_market_display = f"{call_market:.4f}" if call_market is not None else "N/A"
            put_market_display = f"{put_market:.4f}" if put_market is not None else "N/A"
            
            st.subheader("Latest Option Prices (MC-Based)")
            col1, col2 = st.columns(2)
            with col1:
                # Call Price (market) above Call Value (MC Binomial Tree)
                st.markdown(f"<div style='background-color:#2980b9;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_market_display}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='background-color:#2ecc40;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Value (MC Binomial)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_display}</span></div>", unsafe_allow_html=True)
            with col2:
                # Put Price (market) above Put Value (MC Binomial Tree)
                st.markdown(f"<div style='background-color:#c0392b;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_market_display}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='background-color:#e74c3c;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Value (MC Binomial)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_display}</span></div>", unsafe_allow_html=True)

            # --- MC Binomial Tree Structure Visualization ---
            st.subheader("Binomial Tree Structure (MC Probabilities)")
            
            # Create a simplified tree visualization with conditional MC probabilities
            max_levels = min(6, int(n_steps_mc))
            dt = T / int(n_steps_mc)
            u = np.exp(empirical_vol * np.sqrt(dt))
            d = 1 / u
            
            fig_tree_mc, ax = plt.subplots(figsize=(14, 10))
            
            # Plot tree structure with conditional MC probabilities
            for level in range(max_levels + 1):
                for node in range(level + 1):
                    # Calculate stock price at this node
                    stock_price = spot * (u ** (level - node)) * (d ** node)
                    
                    # Calculate conditional MC probability for this specific price level
                    p_mc_conditional = run_mc_simulations(stock_price, hist_data, 5000)
                    
                    # Calculate option value (simplified)
                    if level == max_levels:  # Terminal nodes
                        call_value = max(stock_price - K, 0)
                        put_value = max(K - stock_price, 0)
                    else:
                        # For non-terminal nodes, use a simplified calculation
                        call_value = call_val_mc * (stock_price / spot)  # Approximation
                        put_value = put_val_mc * (K / stock_price)  # Approximation
                    
                    # Position in tree
                    x_pos = level
                    y_pos = node - level/2
                    
                    # Plot node
                    ax.plot(x_pos, y_pos, 'o', markersize=8, color='purple')
                    
                    # Add stock price label
                    ax.text(x_pos, y_pos + 0.15, f'S: ${stock_price:.2f}', 
                           ha='center', va='bottom', fontsize=8)
                    
                    # Add option value label
                    ax.text(x_pos, y_pos - 0.15, f'C: ${call_value:.2f}\nP: ${put_value:.2f}', 
                           ha='center', va='top', fontsize=7)
                    
                    # Connect to parent nodes and add conditional MC probabilities
                    if level > 0:
                        if node > 0:  # Connect to up-move parent
                            ax.plot([x_pos-1, x_pos], [y_pos-0.5, y_pos], 'k-', alpha=0.5)
                            # Add up probability
                            ax.text((x_pos-1 + x_pos)/2, (y_pos-0.5 + y_pos)/2 + 0.1, 
                                   f'p={p_mc_conditional:.3f}', ha='center', va='bottom', fontsize=7, 
                                   bbox=dict(boxstyle='round,pad=0.2', facecolor='lightgreen', alpha=0.7))
                        if node < level:  # Connect to down-move parent
                            ax.plot([x_pos-1, x_pos], [y_pos+0.5, y_pos], 'k-', alpha=0.5)
                            # Add down probability
                            ax.text((x_pos-1 + x_pos)/2, (y_pos+0.5 + y_pos)/2 - 0.1, 
                                   f'1-p={1-p_mc_conditional:.3f}', ha='center', va='top', fontsize=7,
                                   bbox=dict(boxstyle='round,pad=0.2', facecolor='lightcoral', alpha=0.7))
            
            ax.set_xlabel('Time Steps')
            ax.set_ylabel('Price Levels')
            ax.set_title(f'Conditional MC Binomial Tree Structure (First {max_levels} Levels)\nS₀=${spot:.2f}, K=${K:.2f}, σ={empirical_vol:.3f}, T={T:.3f}')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(-0.5, max_levels + 0.5)
            ax.set_ylim(-max_levels/2 - 0.5, max_levels/2 + 0.5)
            
            # Add legend
            ax.text(0.02, 0.98, 'S: Stock Price\nC: Call Value\nP: Put Value\np: Conditional MC Up Probability\n1-p: Conditional MC Down Probability', 
                   transform=ax.transAxes, fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            st.pyplot(fig_tree_mc, use_container_width=True, clear_figure=True)
            
            # Show MC analysis summary
            st.subheader("Monte Carlo Analysis Summary")
            st.info(f"• Historical data period: 2 years")
            st.info(f"• MC simulations per node: 5000")
            st.info(f"• Price tolerance for conditional analysis: ±1%")
            st.info(f"• Conditional probabilities calculated based on similar price levels")
            
        except Exception as e:
            st.error(f"Error fetching historical data: {e}")
            st.info("Please ensure the ticker symbol is valid and try again.")

# --- Monte Carlo Tab ---
with tabs[3]:
    st.header("Monte Carlo Model")
    n_sim_raw = st.number_input("Number of Simulations", min_value=100, max_value=100000, value=10000, step=100)
    try:
        n_sim = int(float(n_sim_raw))
    except Exception:
        n_sim = 10000
    if st.button("Calculate Monte Carlo"):
        call_val = monte_carlo_price(spot, K, T, r, vol, 'call', n_sim)
        put_val = monte_carlo_price(spot, K, T, r, vol, 'put', n_sim)
        expiry_str = expiry_date.strftime('%Y-%m-%d')
        call_market = get_option_market_price(ticker_str, expiry_str, K, 'call')
        put_market = get_option_market_price(ticker_str, expiry_str, K, 'put')
        
        # Beautiful styled pricing display
        call_display = f"{call_val:.4f}"
        put_display = f"{put_val:.4f}"
        call_market_display = f"{call_market:.4f}" if call_market is not None else "N/A"
        put_market_display = f"{put_market:.4f}" if put_market is not None else "N/A"
        
        st.subheader("Latest Option Prices")
        col1, col2 = st.columns(2)
        with col1:
            # Call Price (market) above Call Value (Monte Carlo)
            st.markdown(f"<div style='background-color:#2980b9;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_market_display}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#2ecc40;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Call Value (Monte Carlo)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{call_display}</span></div>", unsafe_allow_html=True)
        with col2:
            # Put Price (market) above Put Value (Monte Carlo)
            st.markdown(f"<div style='background-color:#c0392b;padding:15px;border-radius:10px;text-align:center;margin-bottom:10px;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Price (Market)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_market_display}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#e74c3c;padding:15px;border-radius:10px;text-align:center;'><span style='color:white;font-size:16px;font-weight:bold;'>Put Value (Monte Carlo)</span><br><span style='color:white;font-size:20px;font-weight:bold;'>{put_display}</span></div>", unsafe_allow_html=True)

        # --- Monte Carlo Process Visualization ---
        st.subheader("Monte Carlo Process Visualization")
        
        # Generate sample price paths
        np.random.seed(42)
        n_paths_viz = 50  # Show fewer paths for clarity
        n_steps_viz = 100
        dt_viz = T / n_steps_viz
        
        # Generate price paths
        price_paths = np.zeros((n_paths_viz, n_steps_viz + 1))
        price_paths[:, 0] = spot
        
        for i in range(n_steps_viz):
            Z = np.random.standard_normal(n_paths_viz)
            price_paths[:, i + 1] = price_paths[:, i] * np.exp((r - 0.5 * vol ** 2) * dt_viz + vol * np.sqrt(dt_viz) * Z)
        
        # Plot sample price paths
        fig_paths, ax = plt.subplots(figsize=(12, 6))
        time_steps = np.linspace(0, T, n_steps_viz + 1)
        
        for i in range(n_paths_viz):
            ax.plot(time_steps, price_paths[i, :], alpha=0.3, linewidth=0.5)
        
        # Highlight strike price
        ax.axhline(y=K, color='red', linestyle='--', linewidth=2, label=f'Strike Price: ${K:.2f}')
        ax.axhline(y=spot, color='green', linestyle='--', linewidth=2, label=f'Current Price: ${spot:.2f}')
        
        # Adjust y-axis limits to be 5% above max and 5% below min
        y_min = price_paths.min()
        y_max = price_paths.max()
        ax.set_ylim(y_min * 0.95, y_max * 1.05)
        
        ax.set_xlabel('Time to Expiry (years)')
        ax.set_ylabel('Stock Price ($)')
        ax.set_title(f'Sample Monte Carlo Price Paths (n={n_paths_viz})')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig_paths, use_container_width=True, clear_figure=True)
        # All other Monte Carlo visualizations and explanations removed as requested.


with tabs[4]:
    st.header("Greeks Dashboard")
    st.write("Line plots and 3D Delta Surface for Greeks.")
    grid_steps = 12
    spot_range = np.linspace(spot * 0.8, spot * 1.2, grid_steps)
    # Calculate Greeks for line plot
    delta_vals = []
    gamma_vals = []
    theta_vals = []
    vega_vals = []
    rho_vals = []
    for s in spot_range:
        payload = {"S": s, "K": K, "T": T, "r": r, "sigma": vol, "option_type": "call", "q": 0.0}
        delta_args = {k: payload[k] for k in ["S", "K", "T", "r", "sigma", "option_type"]}
        base_args = {k: payload[k] for k in ["S", "K", "T", "r", "sigma"]}
        delta_vals.append(delta(**delta_args))
        gamma_vals.append(gamma(**base_args))
        theta_vals.append(theta(**base_args))
        vega_vals.append(vega(**base_args))
        rho_vals.append(rho(**base_args))
    # Side by side charts
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(spot_range, delta_vals, label="Delta")
        ax.plot(spot_range, gamma_vals, label="Gamma")
        ax.plot(spot_range, theta_vals, label="Theta")
        ax.plot(spot_range, vega_vals, label="Vega")
        ax.plot(spot_range, rho_vals, label="Rho")
        ax.set_xlabel("Spot Price (S)")
        ax.set_ylabel("Greek Value")
        ax.set_title("Greeks vs Spot Price (fixed Volatility)")
        ax.legend()
        st.pyplot(fig, use_container_width=True, clear_figure=True)
    with col2:
        fig3d = plt.figure(figsize=(7, 5))
        ax3d = fig3d.add_subplot(111, projection='3d')
        sigma_range = np.linspace(vol_min, vol_max, grid_steps)
        S_grid, sigma_grid = np.meshgrid(spot_range, sigma_range)
        delta_grid = np.zeros_like(S_grid)
        for i in range(S_grid.shape[0]):
            for j in range(S_grid.shape[1]):
                delta_grid[i, j] = delta(S_grid[i, j], K, T, r, sigma_grid[i, j], "call")
        ax3d.plot_surface(S_grid, sigma_grid, delta_grid, cmap='viridis')
        ax3d.set_xlabel('Spot Price (S)', labelpad=8, fontsize=10)
        ax3d.set_ylabel('Volatility (sigma)', labelpad=8, fontsize=10)
        ax3d.set_zlabel('Delta', labelpad=8, fontsize=10)
        ax3d.set_title('3D Delta Surface', fontsize=10, pad=1)
        # Shift the chart container up
        plt.subplots_adjust(left=0.15, right=0.85, top=0.98, bottom=0.15)
        st.pyplot(fig3d, use_container_width=True, clear_figure=True)

with tabs[5]:
    st.header("Implied Volatility Smile")
    st.write("Fetch option chain from Yahoo Finance and plot IV smile.")
    ticker = st.text_input("Ticker", value="AAPL")
    # Calculate the 3rd Friday of next month
    today = date.today()
    year = today.year + (1 if today.month == 12 else 0)
    month = today.month + 1 if today.month < 12 else 1
    # Find all Fridays in the next month
    first_of_month = date(year, month, 1)
    fridays = [first_of_month + timedelta(days=(4 - first_of_month.weekday() + 7 * i) % 7 + 7 * i)
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
                if strikes and ivs:
                    st.line_chart({"Strike": strikes, "Implied Vol": ivs})
                else:
                    st.error("No option data available for the specified ticker and expiry date.")
            except Exception as e:
                st.error(f"Error fetching option data: {e}")
                st.info("This may be due to yfinance API issues or no options available for the specified parameters.") 