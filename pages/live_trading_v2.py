"""
Live Trading Page V2 - Daemon-Based

Simplified interface that works with the background trading daemon.
Automatically evaluates ALL strategies and runs continuously.
"""

import streamlit as st
import sys
sys.path.append('..')
from auth import require_auth
require_auth()

import pandas as pd
from datetime import datetime
import subprocess
import os
import signal

from src.trading.state_manager import StateManager

# Page configuration
st.set_page_config(
    page_title="Live Trading V2",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Automated Live Trading (V2)")
st.markdown("### Continuous Background Trading with Persistent State")
st.markdown("---")

# Initialize state manager
state_manager = StateManager()

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

# Tickers Input
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
    max_value=3600,
    value=300,
    step=60,
    help="How often to check for new signals (300 = 5 minutes)"
)

# Save Configuration Button
if st.sidebar.button("💾 Save Configuration", type="primary"):
    state_manager.save_trading_config(
        tickers=symbols,
        paper_trading=paper_trading,
        initial_capital=initial_capital,
        risk_per_trade=risk_per_trade,
        max_positions=max_positions,
        check_interval=check_interval
    )
    st.sidebar.success("✅ Configuration saved!")

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(["🎛️ Control Panel", "📊 Strategy Results", "💼 Portfolio", "📈 Trade History"])

with tab1:
    st.markdown("### Trading Control Panel")
    
    # Load current config
    current_config = state_manager.get_trading_config()
    trading_state = state_manager.get_trading_state()
    is_active = trading_state.get('is_active', False)
    
    # Display current status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_color = "🟢" if is_active else "🔴"
        st.metric("Trading Status", f"{status_color} {'ACTIVE' if is_active else 'STOPPED'}")
    
    with col2:
        if trading_state.get('last_check'):
            st.metric("Last Check", trading_state['last_check'])
        else:
            st.metric("Last Check", "Never")
    
    with col3:
        if current_config:
            st.metric("Configured Tickers", len(current_config['tickers']))
        else:
            st.metric("Configured Tickers", 0)
    
    st.markdown("---")
    
    # Show current configuration
    if current_config:
        st.markdown("#### Current Configuration")
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.info(f"""
            **Tickers:** {', '.join(current_config['tickers'])}
            
            **Mode:** {'📝 Paper Trading' if current_config['paper_trading'] else '💰 LIVE Trading'}
            
            **Capital:** ${current_config['initial_capital']:,.2f}
            """)
        
        with config_col2:
            st.info(f"""
            **Risk/Trade:** {current_config['risk_per_trade']*100:.1f}%
            
            **Max Positions:** {current_config['max_positions']}
            
            **Check Interval:** {current_config['check_interval']} seconds
            """)
    else:
        st.warning("⚠️ No configuration saved. Please configure and save settings in the sidebar.")
    
    st.markdown("---")
    
    # Control buttons
    st.markdown("### Start/Stop Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ START TRADING", type="primary", disabled=is_active or not current_config):
            state_manager.set_trading_active(True)
            st.success("✅ Trading activated! The background daemon will begin executing trades.")
            st.info("💡 The daemon runs independently. You can close this page and trading will continue.")
            st.rerun()
    
    with col2:
        if st.button("⏹️ STOP TRADING", disabled=not is_active):
            state_manager.set_trading_active(False)
            st.warning("⚠️ Trading stopped. The daemon will halt at the next check.")
            st.rerun()
    
    st.markdown("---")
    
    # Daemon information
    st.markdown("### 🔧 Background Daemon")
    st.info("""
    **How it works:**
    
    1. **Start the daemon** by running: `python -m src.trading.trading_daemon`
    2. **Configure trading** in the sidebar and save
    3. **Start trading** using the button above
    4. **The daemon runs continuously**, even when you close your laptop
    5. **All strategies are automatically evaluated** for each ticker
    6. **The best strategy is selected** and used for trading
    7. **Stop trading** anytime using the button above
    
    **The daemon is independent of this UI** - it runs as a separate process and persists state in a database.
    """)
    
    # Daemon status check
    st.markdown("#### Daemon Status")
    daemon_running = False
    daemon_status_msg = "Unknown"
    
    try:
        # Check if PID file exists and process is running
        if os.path.exists('data/daemon.pid'):
            with open('data/daemon.pid', 'r') as f:
                pid = f.read().strip()
            # Check if process with this PID exists
            try:
                os.kill(int(pid), 0)  # Send signal 0 to check if process exists
                daemon_running = True
                daemon_status_msg = f"Running (PID: {pid})"
            except (OSError, ValueError):
                daemon_status_msg = "PID file exists but process not found"
        else:
            # Check log file for recent activity
            if os.path.exists('data/trading_daemon.log'):
                with open('data/trading_daemon.log', 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        # Check if log was updated recently (within last 5 minutes)
                        import re
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', last_line)
                        if timestamp_match:
                            from datetime import datetime, timedelta
                            log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                            if datetime.now() - log_time < timedelta(minutes=5):
                                daemon_running = True
                                daemon_status_msg = "Running (detected from logs)"
                            else:
                                daemon_status_msg = "No recent activity in logs"
                        else:
                            daemon_status_msg = "Log file exists but unable to parse"
                    else:
                        daemon_status_msg = "Log file is empty"
            else:
                daemon_status_msg = "No PID file or log file found"
    except Exception as e:
        daemon_status_msg = f"Error checking status: {str(e)}"
    
    if daemon_running:
        st.success(f"✅ Daemon is running - {daemon_status_msg}")
    else:
        st.warning(f"⚠️ Daemon not detected - {daemon_status_msg}")
        st.info("Start it with: `./start_daemon.sh` or `python -m src.trading.trading_daemon`")

with tab2:
    st.markdown("### 📊 Strategy Evaluation Results")
    st.info("All 11 strategies are automatically evaluated for each ticker. Results are persisted across restarts.")
    
    if current_config:
        for ticker in current_config['tickers']:
            st.markdown(f"#### {ticker}")
            
            # Get best strategy
            best_strategy = state_manager.get_best_strategy(ticker)
            
            if best_strategy:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Best Strategy", best_strategy['strategy_name'])
                with col2:
                    st.metric(f"Best {best_strategy['metric_name']}", f"{best_strategy['score']:.3f}")
                with col3:
                    st.metric("Evaluated", best_strategy['evaluation_date'].split()[0])
                
                # Get all evaluations
                all_evals = state_manager.get_all_evaluations(ticker)
                
                if all_evals:
                    with st.expander(f"View All Strategy Results for {ticker}"):
                        eval_data = []
                        for eval_result in all_evals:
                            metrics = eval_result['metrics']
                            eval_data.append({
                                'Strategy': eval_result['strategy_name'],
                                'Return %': f"{metrics['total_return_pct']:.2f}",
                                'Sharpe': f"{metrics['sharpe_ratio']:.3f}",
                                'Win Rate %': f"{metrics['win_rate_pct']:.1f}",
                                'Profit Factor': f"{metrics['profit_factor']:.2f}",
                                'Max Drawdown %': f"{metrics['max_drawdown_pct']:.2f}"
                            })
                        
                        eval_df = pd.DataFrame(eval_data)
                        st.dataframe(eval_df, hide_index=True, width="stretch")
            else:
                st.warning(f"No evaluation results for {ticker}. Start trading to trigger automatic evaluation.")
            
            st.markdown("---")
    else:
        st.warning("Configure and save trading settings to see strategy results.")

with tab3:
    st.markdown("### 💼 Portfolio Overview")
    
    st.info("""
    **Note:** Portfolio data is managed by Alpaca and viewed through their API.
    The daemon executes trades based on the best strategies for each ticker.
    """)
    
    if st.button("🔄 Load Portfolio from Alpaca"):
        try:
            from src.trading.live_trader import LiveTrader
            from src.strategies.sma_crossover import SMACrossoverStrategy
            
            # Create a minimal trader just to get portfolio
            trader = LiveTrader(
                strategies={'SMA': SMACrossoverStrategy()},
                symbols=['AAPL'],
                initial_capital=10000,
                paper_trading=paper_trading
            )
            
            summary = trader.get_portfolio_summary()
            
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
                    st.dataframe(positions_df, hide_index=True, width="stretch")
                else:
                    st.info("No open positions")
        except Exception as e:
            st.error(f"Error loading portfolio: {str(e)}")

with tab4:
    st.markdown("### 📈 Trade History")
    st.info("All trades executed by the daemon are recorded here.")
    
    # Filter options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_ticker = st.selectbox(
            "Filter by Ticker",
            ["All Tickers"] + (current_config['tickers'] if current_config else [])
        )
    
    with col2:
        limit = st.number_input("Show last N trades", min_value=10, max_value=500, value=50)
    
    if st.button("📊 Load Trade History"):
        ticker_filter = None if selected_ticker == "All Tickers" else selected_ticker
        trades = state_manager.get_trade_history(ticker=ticker_filter, limit=limit)
        
        if trades:
            trades_df = pd.DataFrame(trades)
            
            # Format columns
            trades_df['price'] = trades_df['price'].apply(lambda x: f"${x:.2f}")
            trades_df['signal'] = trades_df['signal'].apply(
                lambda x: "🟢 BUY" if x == 1 else "🔴 SELL" if x == -1 else "⚪ HOLD"
            )
            
            st.dataframe(trades_df, hide_index=True, width="stretch")
            
            # Summary stats
            st.markdown("#### Trade Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Trades", len(trades))
            with col2:
                buy_count = len([t for t in trades if t['action'] == 'BUY'])
                st.metric("Buy Orders", buy_count)
            with col3:
                sell_count = len([t for t in trades if t['action'] == 'SELL'])
                st.metric("Sell Orders", sell_count)
        else:
            st.info("No trades recorded yet. Start trading to see trade history.")

# Footer
st.markdown("---")
st.markdown("""
### 💡 Key Features:

- **Automatic Strategy Evaluation**: All 11 strategies are tested for each ticker
- **Best Strategy Selection**: The system automatically picks the best performer
- **Persistent State**: Trading continues even after closing your laptop
- **Background Daemon**: Independent process that runs continuously
- **Real-time Monitoring**: View status, results, and history anytime

### 🚀 Quick Start:

1. Configure your trading parameters in the sidebar
2. Click "Save Configuration"
3. Run the daemon: `python -m src.trading.trading_daemon`
4. Click "START TRADING"
5. Monitor your trades in the Trade History tab
""")
