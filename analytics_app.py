import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from models import OptionInput, SessionLocal
from sqlalchemy import func

st.title("Option Pricing Analytics Dashboard")

session = SessionLocal()

# Most-used strikes
st.header("Most-Used Strikes")
strike_counts = session.query(OptionInput.K, func.count(OptionInput.K)).group_by(OptionInput.K).all()
if strike_counts:
    df_strikes = pd.DataFrame(strike_counts, columns=["Strike", "Count"])
    st.bar_chart(df_strikes.set_index("Strike"))
else:
    st.info("No strike data available.")

# Most-used vol ranges
st.header("Most-Used Volatility Ranges")
vol_bins = np.arange(0, 1.05, 0.05)
vol_counts = session.query(OptionInput.sigma).all()
if vol_counts:
    vols = [v[0] for v in vol_counts]
    hist, bins = np.histogram(vols, bins=vol_bins)
    st.bar_chart(pd.DataFrame({"Volatility": bins[:-1], "Count": hist}).set_index("Volatility"))
else:
    st.info("No volatility data available.")

# User activity heatmap (strike vs vol)
st.header("User Activity Heatmap (Strike × Volatility)")
inputs = session.query(OptionInput.K, OptionInput.sigma).all()
if inputs:
    df = pd.DataFrame(inputs, columns=["Strike", "Volatility"])
    heatmap, xedges, yedges = np.histogram2d(df["Strike"], df["Volatility"], bins=[20, 20])
    fig, ax = plt.subplots()
    c = ax.imshow(heatmap.T, origin='lower', aspect='auto',
                  extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]], cmap='viridis')
    ax.set_xlabel('Strike')
    ax.set_ylabel('Volatility')
    ax.set_title('User Activity Heatmap')
    fig.colorbar(c, ax=ax, label='Count')
    st.pyplot(fig)
else:
    st.info("No user activity data available.")

session.close() 