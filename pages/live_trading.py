"""
Live Trading Page

Automated trading with strategy selection and execution via Alpaca.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import time

sys.path.append('..')

from src.trading.live_trader import LiveTrader
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.breakout_strategy import BreakoutStrategy
from src.strategies.vwap_strategy import VWAPStrategy
from src.strategies.pairs_trading import PairsTradingStrategy
from src.strategies.ml_strategy import MLStrategy
from src.strategies.adaptive_ml_strategy import AdaptiveMLStrategy

# Page configuration
st.set_page_config(
    page_title="Live Trading",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Automated Live Trading")
st.markdown("---")

# Initialize session state
if 'trader' not in st.session_state:
    st.session_state.trader = None
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False

# Sidebar Configuration
st.sidebar.header("⚙️ Trading Configuration")

# Trading Mode
trading_mode = st.sidebar.radio(
    "Trading Mode",
    ["Paper Trading (Recommended)", "Live Trading (Real Money)"],
    help="Start with paper trading to test your strategies"
)
paper_trading = trading_mode.startswith("Paper")

if not paper_trading:
    st.sidebar.warning("⚠️ **LIVE TRADING WARNING**: Real money will be used!")

# Symbols Input
symbols_input = st.sidebar.text_area(
    "Stock Symbols (one per line)",
    value="AAPL\nMSFT\nTSLA\nNVDA\nAMD",
    help="Enter stock symbols you want to trade, one per line"
)
symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]

# Strategy Selection
st.sidebar.markdown("### Select Strategies to Evaluate")
selected_strategies = st.sidebar.multiselect(
    "Choose strategies",
    ["SMA Crossover", "RSI", "MACD", "Bollinger Bands", "Momentum", 
     "Mean Reversion", "Breakout", "VWAP", "Pairs Trading", "ML Strategy", "Adaptive ML"],
    default=["SMA Crossover", "RSI", "MACD", "Momentum"],
    help="Select multiple strategies - the best will be chosen for each stock"
)

# Risk Parameters
st.sidebar.markdown("### Risk Management")
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=100,
    max_value=1000000,
    value=500,
    step=100
)

risk_per_trade = st.sidebar.slider(
    "Risk Per Trade (%)",
    min_value=1,
    max_value=10,
    value=2,
    help="Maximum % of capital to risk per trade"
) / 100

max_positions = st.sidebar.slider(
    "Max Concurrent Positions",
    min_value=1,
    max_value=10,
    value=5,
    help="Maximum number of open positions at once"
)

# Evaluation Settings
st.sidebar.markdown("### Evaluation Settings")
lookback_days = st.sidebar.slider(
    "Backtest Lookback (days)",
    min_value=30,
    max_value=730,
    value=365,
    help="Historical data period for strategy evaluation"
)

optimization_metric = st.sidebar.selectbox(
    "Optimization Metric",
    ["sharpe_ratio", "total_return_pct", "profit_factor"],
    help="Metric to use for selecting best strategy"
)

# Check Interval
check_interval = st.sidebar.number_input(
    "Signal Check Interval (seconds)",
    min_value=60,
    max_value=3600,
    value=300,
    help="How often to check for new signals (300 = 5 minutes)"
)

# Create strategy instances
def get_strategies():
    strategies = {}
    if "SMA Crossover" in selected_strategies:
        strategies["SMA Crossover"] = SMACrossoverStrategy()
    if "RSI" in selected_strategies:
        strategies["RSI"] = RSIStrategy()
    if "MACD" in selected_strategies:
        strategies["MACD"] = MACDStrategy()
    if "Bollinger Bands" in selected_strategies:
        strategies["Bollinger Bands"] = BollingerBandsStrategy()
    if "Momentum" in selected_strategies:
        strategies["Momentum"] = MomentumStrategy()
    if "Mean Reversion" in selected_strategies:
        strategies["Mean Reversion"] = MeanReversionStrategy()
    if "Breakout" in selected_strategies:
        strategies["Breakout"] = BreakoutStrategy()
    if "VWAP" in selected_strategies:
        strategies["VWAP"] = VWAPStrategy()
    if "Pairs Trading" in selected_strategies:
        strategies["Pairs Trading"] = PairsTradingStrategy()
    if "ML Strategy" in selected_strategies:
        strategies["ML Strategy"] = MLStrategy()
    if "Adaptive ML" in selected_strategies:
        strategies["Adaptive ML"] = AdaptiveMLStrategy(use_sentiment=False)
    return strategies

# Main Content
tab1, tab2, tab3 = st.tabs(["📊 Strategy Evaluation", "🤖 Live Trading", "💼 Portfolio"])

with tab1:
    st.markdown("### Step 1: Evaluate Strategies")
    st.info("""
    **How it works:**
    1. Select your target stocks and strategies
    2. Click "Evaluate Strategies" to run backtests
    3. System will identify the best strategy for each stock
    4. Move to Live Trading tab to start automated trading
    """)
    
    if st.button("🔍 Evaluate Strategies", type="primary", use_container_width=True):
        if not symbols:
            st.error("Please enter at least one stock symbol")
        elif not selected_strategies:
            st.error("Please select at least one strategy")
        else:
            with st.spinner(f"Evaluating {len(selected_strategies)} strategies on {len(symbols)} stocks..."):
                try:
                    # Create strategies
                    strategies = get_strategies()
                    
                    # Create trader
                    trader = LiveTrader(
                        strategies=strategies,
                        symbols=symbols,
                        initial_capital=initial_capital,
                        paper_trading=paper_trading,
                        risk_per_trade=risk_per_trade,
                        max_positions=max_positions
                    )
                    
                    # Evaluate strategies
                    results = trader.evaluate_strategies(
                        lookback_days=lookback_days,
                        metric=optimization_metric
                    )
                    
                    # Store in session state
                    st.session_state.trader = trader
                    st.session_state.evaluation_results = results
                    
                    st.success("✅ Strategy evaluation completed!")
                    
                except Exception as e:
                    st.error(f"Error during evaluation: {str(e)}")
                    st.exception(e)
    
    # Display evaluation results
    if st.session_state.evaluation_results:
        st.markdown("### 🏆 Best Strategies for Each Stock")
        
        results_data = []
        for symbol, data in st.session_state.evaluation_results.items():
            best_strategy = data['best_strategy']
            best_score = data['best_score']
            all_results = data['all_results']
            
            results_data.append({
                'Symbol': symbol,
                'Best Strategy': best_strategy,
                f'Best {optimization_metric}': f"{best_score:.3f}",
                'Strategies Tested': len(all_results)
            })
        
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, hide_index=True, use_container_width=True)
        
        # Detailed results
        with st.expander("📋 Detailed Results by Stock"):
            for symbol, data in st.session_state.evaluation_results.items():
                st.markdown(f"#### {symbol}")
                
                strat_data = []
                for strat_name, strat_results in data['all_results'].items():
                    metrics = strat_results['metrics']
                    strat_data.append({
                        'Strategy': strat_name,
                        'Return %': f"{metrics['total_return_pct']:.2f}",
                        'Sharpe': f"{metrics['sharpe_ratio']:.3f}",
                        'Win Rate %': f"{metrics['win_rate_pct']:.1f}",
                        'Profit Factor': f"{metrics['profit_factor']:.2f}"
                    })
                
                strat_df = pd.DataFrame(strat_data)
                st.dataframe(strat_df, hide_index=True)

with tab2:
    st.markdown("### Step 2: Start Live Trading")
    
    if not st.session_state.trader or not st.session_state.evaluation_results:
        st.warning("⚠️ Please evaluate strategies first (Step 1)")
    else:
        st.info(f"""
        **Ready to trade:**
        - Mode: {'📝 Paper Trading' if paper_trading else '💰 LIVE Trading'}
        - Stocks: {len(symbols)}
        - Max Positions: {max_positions}
        - Risk per Trade: {risk_per_trade*100}%
        - Check Interval: {check_interval} seconds
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start Auto Trading", type="primary", use_container_width=True):
                st.session_state.trading_active = True
        
        with col2:
            if st.button("⏹️ Stop Trading", type="secondary", use_container_width=True):
                st.session_state.trading_active = False
                st.info("Trading stopped")
        
        # Trading loop (simplified for Streamlit)
        if st.session_state.trading_active:
            st.markdown("### 🔄 Trading Active")
            
            # Get current signals
            trader = st.session_state.trader
            
            with st.spinner("Getting signals..."):
                signals = trader.get_current_signals()
            
            # Display signals
            st.markdown("#### 📡 Current Signals")
            signal_data = []
            for symbol, signal in signals.items():
                signal_str = "🟢 BUY" if signal == 1 else "🔴 SELL" if signal == -1 else "⚪ HOLD"
                best_strat = st.session_state.evaluation_results[symbol]['best_strategy']
                signal_data.append({
                    'Symbol': symbol,
                    'Strategy': best_strat,
                    'Signal': signal_str
                })
            
            signal_df = pd.DataFrame(signal_data)
            st.dataframe(signal_df, hide_index=True, use_container_width=True)
            
            # Execute trades button
            if st.button("🔄 Execute Trades", use_container_width=True):
                with st.spinner("Executing trades..."):
                    trades = trader.execute_trades(signals)
                    
                    if trades:
                        st.success(f"✅ Executed {len(trades)} trades")
                        
                        trades_df = pd.DataFrame(trades)
                        st.dataframe(trades_df, hide_index=True)
                    else:
                        st.info("No trades to execute")
            
            st.info(f"⏰ Next check in {check_interval} seconds. Click 'Execute Trades' to trade now, or let it run automatically.")
            
            # Auto-refresh
            time.sleep(5)
            st.rerun()

with tab3:
    st.markdown("### 💼 Portfolio Overview")
    
    if st.session_state.trader:
        if st.button("🔄 Refresh Portfolio", use_container_width=True):
            with st.spinner("Loading portfolio..."):
                summary = st.session_state.trader.get_portfolio_summary()
                
                if summary:
                    # Account metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Portfolio Value", f"${summary['portfolio_value']:,.2f}")
                    with col2:
                        st.metric("Cash", f"${summary['cash']:,.2f}")
                    with col3:
                        st.metric("Buying Power", f"${summary['buying_power']:,.2f}")
                    with col4:
                        st.metric("Positions", summary['positions_count'])
                    
                    # Positions table
                    if summary['positions']:
                        st.markdown("#### Current Positions")
                        positions_df = pd.DataFrame(summary['positions'])
                        positions_df['unrealized_plpc'] = positions_df['unrealized_plpc'].apply(lambda x: f"{x*100:.2f}%")
                        positions_df['unrealized_pl'] = positions_df['unrealized_pl'].apply(lambda x: f"${x:.2f}")
                        positions_df['market_value'] = positions_df['market_value'].apply(lambda x: f"${x:.2f}")
                        positions_df['current_price'] = positions_df['current_price'].apply(lambda x: f"${x:.2f}")
                        
                        st.dataframe(positions_df, hide_index=True, use_container_width=True)
                    else:
                        st.info("No open positions")
                else:
                    st.error("Could not load portfolio summary")
    else:
        st.info("Please evaluate strategies first to connect to your trading account")

# Footer
st.markdown("---")
st.markdown("""
### 📚 How to Use:
1. **Evaluate**: Select stocks and strategies, then evaluate to find the best strategy for each stock
2. **Trade**: Start automated trading with the selected best strategies
3. **Monitor**: Check your portfolio and positions regularly

**Important Notes:**
- Always start with paper trading to test your strategies
- Monitor your positions regularly
- Set appropriate risk limits
- The system checks for signals every N seconds and executes trades automatically
""")
