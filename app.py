"""
Algorithmic Trading Platform - Landing Page & Dashboard

Secure login and navigation hub for all trading features.
"""

import streamlit as st
from auth import check_password

# Page configuration
st.set_page_config(
    page_title="Algo Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        height: 100px;
        font-size: 20px;
        margin: 10px 0;
    }
    .feature-card {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication check
if not check_password():
    st.stop()

# Welcome message after successful login
st.title("📈 Algorithmic Trading Platform")
st.markdown("### Welcome to Your Trading Dashboard")
st.markdown("---")

# Dashboard Content
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Strategy Backtesting</h3>
        <p>Test and compare 11 trading strategies on historical data</p>
        <ul>
            <li>Single strategy analysis</li>
            <li>Multi-strategy comparison</li>
            <li>Performance metrics & charts</li>
            <li>Trade history export</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Launch Backtesting", key="backtest", type="primary"):
        st.switch_page("pages/backtesting.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🤖 Live Trading (Multiple Versions)</h3>
        <p>Choose the version that fits your deployment:</p>
        <ul>
            <li><strong>V2.5 (Cloud)</strong>: Auto-eval all strategies, works on Streamlit Cloud</li>
            <li><strong>V2 (VPS)</strong>: 24/7 operation with background daemon</li>
            <li><strong>V1 (Legacy)</strong>: Manual strategy selection</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col2a, col2b, col2c = st.columns(3)
    with col2a:
        if st.button("☁️ V2.5 Cloud", key="live_v25", type="primary"):
            st.switch_page("pages/live_trading_v2_5.py")
    with col2b:
        if st.button("🖥️ V2 VPS", key="live_v2", type="secondary"):
            st.switch_page("pages/live_trading_v2.py")
    with col2c:
        if st.button("📊 V1", key="live", type="secondary"):
            st.switch_page("pages/live_trading.py")

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>🔍 Diagnostics</h3>
        <p>Debug strategies and analyze signal generation</p>
        <ul>
            <li>Strategy signal analysis</li>
            <li>Indicator values review</li>
            <li>HOLD signal explanation</li>
            <li>Multi-strategy testing</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔬 Run Diagnostics", key="diag", type="primary"):
        st.switch_page("pages/diagnostics.py")

st.markdown("---")

# System Status & Info
st.markdown("### 📊 System Information")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Available Strategies", "11")
    
with col2:
    st.metric("Security Status", "🔒 Protected")
    
with col3:
    st.metric("Cloud Status", "☁️ Active")
    
with col4:
    st.metric("API Status", "✅ Ready")

# Quick Stats
st.markdown("---")
st.markdown("### 🎯 Platform Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Trading Strategies:**
    - SMA Crossover (Trend Following)
    - RSI (Mean Reversion)
    - MACD (Momentum)
    - Bollinger Bands (Volatility)
    - Momentum Strategy
    - Mean Reversion
    - Breakout Strategy
    - VWAP (Volume-Weighted)
    - Pairs Trading
    - ML Strategy (Ensemble)
    - Adaptive ML (Advanced)
    """)

with col2:
    st.markdown("""
    **Platform Capabilities:**
    - Historical backtesting (1+ years)
    - Real-time paper trading
    - Live trading with Alpaca
    - Multi-strategy comparison
    - Risk management tools
    - Portfolio monitoring
    - Signal diagnostics
    - Performance analytics
    - Mobile responsive
    - Secure authentication
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p><strong>Security Notice:</strong> Your session is protected with password authentication. 
    All API keys are securely stored in Streamlit secrets.</p>
    <p>For support, see SECURITY_AUTH.md in the repository.</p>
</div>
""", unsafe_allow_html=True)

# Logout button in sidebar
with st.sidebar:
    st.markdown("### Navigation")
    st.info("Use the buttons on the dashboard to access different features.")
    st.markdown("---")
    if st.button("🚪 Logout"):
        from auth import logout
        logout()
