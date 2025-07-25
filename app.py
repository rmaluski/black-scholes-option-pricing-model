import streamlit as st
from black_scholes import black_scholes_price

st.title("Black-Scholes Option Pricing Model")

st.sidebar.header("Input Parameters")
S = st.sidebar.number_input("Spot price (S)", min_value=0.0, value=100.0)
K = st.sidebar.number_input("Strike price (K)", min_value=0.0, value=100.0)
T = st.sidebar.number_input("Time to maturity (T, years)", min_value=0.0, value=1.0)
r = st.sidebar.number_input("Risk-free rate (r, decimal)", value=0.05)
sigma = st.sidebar.number_input("Volatility (sigma, decimal)", min_value=0.0, value=0.2)
option_type = st.sidebar.selectbox("Option type", ["call", "put"])

if st.sidebar.button("Calculate"):
    price = black_scholes_price(S, K, T, r, sigma, option_type)
    st.subheader(f"{option_type.capitalize()} Option Price")
    st.table({"Price": [f"{price:.4f}"]}) 