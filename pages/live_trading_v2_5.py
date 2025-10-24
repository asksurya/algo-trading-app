"""
Live Trading V2.5 - Streamlit Cloud Compatible

Auto-evaluates all strategies with session-based persistence.
Works on Streamlit Cloud but requires browser to stay open.
"""

import streamlit as st
import sys
sys.path.append('..')
from auth import require_auth
require_auth()

import pandas as pd
from datetime import datetime, timedelta
import time

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
    page_title="Live Trading V2.5",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Automated Live Trading (V2.5 - Cloud)")
st.markdown("### Auto Strategy Evaluation | Session Persistence | Cloud Compatible")
st.markdown("---")

# Initialize session state
if 'trader' not in st.session_state:
    st.session_state.trader = None
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'trading_active' not in st.session_state:
    st.session_state.trading_active = False
if 'last_check_time' not in st.session_state:
    st.session_state.last_check_time = None
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'config_saved' not in st.session_state:
    st.session_state.config_saved = False

# All available strategies
ALL_STRATEGIES = {
    'SMA Crossover': SMACrossoverStrategy,
    'RSI': RSIStrategy,
    'MACD': MACDStrategy,
    'Bollinger Bands': BollingerBandsStrategy,
    'Momentum': MomentumStrategy,
    'Mean Reversion': MeanReversionStrategy,
    'Breakout': BreakoutStrategy,
    'VWAP': VWAPStrategy,
    'Pairs Trading': PairsTradingStrategy,
    'ML Strategy': MLStrategy,
    'Adaptive ML': AdaptiveMLStrategy
}

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
    value="AAPL\nMSFT\nTSLA",
    help="Enter stock symbols you want to trade, one per line"
)
symbols = [s.strip().upper() for s in symbols_input.split('\n') if s.strip()]

# Risk Parameters
st.sidebar.markdown("### Risk Management")
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=100,
    max_value=1000000,
    value=10000,
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

# Check Interval
check_interval = st.sidebar.slider(
    "Signal Check Interval (seconds)",
    min_value=60,
    max_value=600,
    value=120,
    step=30,
    help="How often to check for new signals"
)

# Save Configuration
if st.sidebar.button("💾 Save Configuration", type="primary"):
    st.session_state.config_saved = True
    st.session_state.symbols = symbols
    st.session_state.paper_trading = paper_trading
    st.session_state.initial_capital = initial_capital
    st.session_state.risk_per_trade = risk_per_trade
    st.session_state.max_positions = max_positions
    st.session_state.check_interval = check_interval
    st.sidebar.success("✅ Configuration saved!")

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(["🎛️ Control Panel", "📊 Strategy Results", "💼 Portfolio", "📈 Trade History"])

with tab1:
    st.markdown("### Trading Control Panel")
    
    # Status display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "🟢 ACTIVE" if st.session_state.trading_active else "🔴 STOPPED"
        st.metric("Trading Status", status)
    
    with col2:
        if st.session_state.last_check_time:
            st.metric("Last Check", st.session_state.last_check_time.strftime("%H:%M:%S"))
        else:
            st.metric("Last Check", "Never")
    
    with col3:
        if st.session_state.config_saved:
            st.metric("Configured Tickers", len(st.session_state.symbols))
        else:
            st.metric("Configured Tickers", 0)
    
    st.markdown("---")
    
    # Show current configuration
    if st.session_state.config_saved:
        st.markdown("#### Current Configuration")
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.info(f"""
            **Tickers:** {', '.join(st.session_state.symbols)}
            
            **Mode:** {'📝 Paper Trading' if st.session_state.paper_trading else '💰 LIVE Trading'}
            
            **Capital:** ${st.session_state.initial_capital:,.2f}
            """)
        
        with config_col2:
            st.info(f"""
            **Risk/Trade:** {st.session_state.risk_per_trade*100:.1f}%
            
            **Max Positions:** {st.session_state.max_positions}
            
            **Check Interval:** {st.session_state.check_interval} seconds
            """)
    else:
        st.warning("⚠️ No configuration saved. Please configure and save settings in the sidebar.")
    
    st.markdown("---")
    
    # Evaluate Strategies Button
    if not st.session_state.evaluation_results and st.session_state.config_saved:
        st.markdown("### Step 1: Evaluate Strategies")
        st.info("Click below to automatically evaluate ALL 11 strategies for each ticker.")
        
        if st.button("🔍 Evaluate All Strategies", type="primary"):
            with st.spinner(f"Evaluating 11 strategies on {len(st.session_state.symbols)} tickers..."):
                try:
                    # Create strategy instances
                    strategies = {name: cls() for name, cls in ALL_STRATEGIES.items()}
                    
                    # Create trader
                    trader = LiveTrader(
                        strategies=strategies,
                        symbols=st.session_state.symbols,
                        initial_capital=st.session_state.initial_capital,
                        paper_trading=st.session_state.paper_trading,
                        risk_per_trade=st.session_state.risk_per_trade,
                        max_positions=st.session_state.max_positions
                    )
                    
                    # Evaluate strategies using ALL available historical data
                    results = trader.evaluate_strategies(
                        lookback_days=None,  # Use all available data (up to 20 years)
                        metric='sharpe_ratio'
                    )
                    
                    # Store in session state
                    st.session_state.trader = trader
                    st.session_state.evaluation_results = results
                    
                    st.success("✅ All strategies evaluated! View results in the Strategy Results tab.")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error during evaluation: {str(e)}")
    
    # Trading Controls
    if st.session_state.evaluation_results:
        st.markdown("### Step 2: Start/Stop Trading")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ START TRADING", type="primary", disabled=st.session_state.trading_active):
                st.session_state.trading_active = True
                st.session_state.last_check_time = datetime.now()
                st.success("✅ Trading activated! Keep this browser tab open.")
                st.rerun()
        
        with col2:
            if st.button("⏹️ STOP TRADING", disabled=not st.session_state.trading_active):
                st.session_state.trading_active = False
                st.warning("⚠️ Trading stopped.")
                st.rerun()
        
        st.markdown("---")
        
        # Auto-refresh for active trading
        if st.session_state.trading_active:
            st.markdown("### 🔄 Auto Trading Active")
            st.success(f"✅ Checking for signals every {st.session_state.check_interval} seconds...")
            
            # Check if it's time for next cycle
            time_since_last_check = (datetime.now() - st.session_state.last_check_time).total_seconds()
            
            if time_since_last_check >= st.session_state.check_interval:
                # Execute trading cycle
                try:
                    with st.spinner("Getting signals and executing trades..."):
                        # Get signals
                        signals = st.session_state.trader.get_current_signals()
                        
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
                        st.dataframe(signal_df, hide_index=True)
                        
                        # Execute trades
                        trades = st.session_state.trader.execute_trades(signals)
                        
                        if trades:
                            st.success(f"✅ Executed {len(trades)} trades!")
                            # Add to history
                            for trade in trades:
                                trade['timestamp'] = datetime.now()
                                st.session_state.trade_history.append(trade)
                            
                            # Display trades
                            trades_df = pd.DataFrame(trades)
                            st.dataframe(trades_df, hide_index=True)
                        else:
                            st.info("ℹ️ No trades executed (all HOLD or positions full)")
                        
                        # Update last check time
                        st.session_state.last_check_time = datetime.now()
                    
                except Exception as e:
                    st.error(f"Error in trading cycle: {str(e)}")
            
            # Show countdown to next check
            seconds_until_next = max(0, st.session_state.check_interval - int(time_since_last_check))
            st.info(f"⏰ Next check in {seconds_until_next} seconds...")
            
            # Auto-refresh the page
            time.sleep(2)
            st.rerun()
        
        else:
            st.markdown("### ⏸️ Trading Stopped")
            st.info("Click 'START TRADING' to begin automated trading.")
    
    elif not st.session_state.config_saved:
        st.warning("⚠️ Please configure and save your settings first.")
    
    # Cloud compatibility notice
    st.markdown("---")
    st.markdown("### ⚡ Cloud Compatibility")
    st.info("""
    **This version (V2.5) is optimized for Streamlit Cloud:**
    
    ✅ Auto-evaluates ALL 11 strategies
    ✅ Selects best strategy per ticker
    ✅ Session-based persistence
    ✅ Auto-refresh while trading
    
    ⚠️ **Important**: Keep this browser tab open while trading is active.
    Closing the tab will stop trading. For 24/7 operation, deploy V2 to a VPS.
    """)

with tab2:
    st.markdown("### 📊 Strategy Evaluation Results")
    
    if st.session_state.evaluation_results:
        st.info("All 11 strategies have been evaluated. Best strategy selected for each ticker.")
        
        # Summary table
        st.markdown("#### 🏆 Best Strategies")
        results_data = []
        for symbol, data in st.session_state.evaluation_results.items():
            results_data.append({
                'Symbol': symbol,
                'Best Strategy': data['best_strategy'],
                'Sharpe Ratio': f"{data['best_score']:.3f}",
                'Strategies Tested': len(data['all_results'])
            })
        
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, hide_index=True, use_container_width=True)
        
        # Detailed results per ticker
        for symbol, data in st.session_state.evaluation_results.items():
            with st.expander(f"📋 All Strategy Results for {symbol}"):
                strat_data = []
                for strat_name, strat_results in data['all_results'].items():
                    metrics = strat_results['metrics']
                    strat_data.append({
                        'Strategy': strat_name,
                        'Return %': f"{metrics['total_return_pct']:.2f}",
                        'Sharpe': f"{metrics['sharpe_ratio']:.3f}",
                        'Win Rate %': f"{metrics['win_rate_pct']:.1f}",
                        'Profit Factor': f"{metrics['profit_factor']:.2f}",
                        'Max Drawdown %': f"{metrics['max_drawdown_pct']:.2f}"
                    })
                
                strat_df = pd.DataFrame(strat_data)
                # Sort by Sharpe ratio
                strat_df = strat_df.sort_values('Sharpe', ascending=False)
                st.dataframe(strat_df, hide_index=True, use_container_width=True)
    else:
        st.warning("No evaluation results yet. Go to Control Panel and click 'Evaluate All Strategies'.")

with tab3:
    st.markdown("### 💼 Portfolio Overview")
    
    if st.session_state.trader:
        if st.button("🔄 Refresh Portfolio"):
            try:
                summary = st.session_state.trader.get_portfolio_summary()
                
                if summary:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Portfolio Value", f"${summary['portfolio_value']:,.2f}")
                    with col2:
                        st.metric("Cash", f"${summary['cash']:,.2f}")
                    with col3:
                        st.metric("Buying Power", f"${summary['buying_power']:,.2f}")
                    with col4:
                        st.metric("Positions", summary['positions_count'])
                    
                    if summary['positions']:
                        st.markdown("#### Current Positions")
                        positions_df = pd.DataFrame(summary['positions'])
                        st.dataframe(positions_df, hide_index=True, use_container_width=True)
                    else:
                        st.info("No open positions")
            except Exception as e:
                st.error(f"Error loading portfolio: {str(e)}")
    else:
        st.info("Evaluate strategies first to connect to your trading account.")

with tab4:
    st.markdown("### 📈 Trade History")
    
    if st.session_state.trade_history:
        st.info(f"Total trades this session: {len(st.session_state.trade_history)}")
        
        trades_df = pd.DataFrame(st.session_state.trade_history)
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(trades_df, hide_index=True, use_container_width=True)
        
        # Summary stats
        st.markdown("#### Trade Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trades", len(st.session_state.trade_history))
        with col2:
            buy_count = len([t for t in st.session_state.trade_history if t['action'] == 'BUY'])
            st.metric("Buy Orders", buy_count)
        with col3:
            sell_count = len([t for t in st.session_state.trade_history if t['action'] == 'SELL'])
            st.metric("Sell Orders", sell_count)
    else:
        st.info("No trades executed yet. Start trading to see trade history.")
        st.warning("⚠️ Note: Trade history is session-based and will be lost when you close the browser.")

# Footer
st.markdown("---")
st.markdown("""
### 💡 Key Features (V2.5):

- **Automatic Evaluation**: All 11 strategies tested automatically
- **Best Selection**: System picks the best performer for each ticker
- **Session Persistence**: Data preserved during your session
- **Auto-Refresh**: Continuous trading while browser is open
- **Cloud Compatible**: Works on Streamlit Cloud

### ⚠️ Important Limitations:

- **Browser must stay open** - Closing the tab stops trading
- **Session-based** - Data lost when browser closes
- **For 24/7 operation** - Deploy V2 (full version) to a VPS

### 🚀 Quick Start:

1. Configure trading parameters in sidebar
2. Click "Save Configuration"
3. Click "Evaluate All Strategies" (one-time, ~5-10 min)
4. Click "START TRADING"
5. **Keep this tab open** for continuous trading
""")
