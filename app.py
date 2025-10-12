"""
Algorithmic Trading GUI Application

A user-friendly web interface for backtesting and analyzing trading strategies.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys

sys.path.append('.')

from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_fetcher import DataFetcher
from src.utils.visualizer import Visualizer

# Page configuration
st.set_page_config(
    page_title="Algo Trading Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 0rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("📈 Algorithmic Trading Platform")
st.markdown("---")

# Sidebar - Strategy Configuration
st.sidebar.header("⚙️ Configuration")

# Strategy Selection
strategy_type = st.sidebar.selectbox(
    "Select Strategy",
    ["SMA Crossover", "RSI", "MACD"],
    help="Choose a trading strategy to backtest"
)

# Symbol Input
symbol = st.sidebar.text_input(
    "Stock Symbol",
    value="AAPL",
    help="Enter a valid stock ticker symbol"
).upper()

# Date Range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime(2023, 1, 1),
        max_value=datetime.now()
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now() - timedelta(days=1),
        max_value=datetime.now()
    )

# Initial Capital
initial_capital = st.sidebar.number_input(
    "Initial Capital ($)",
    min_value=1000,
    max_value=10000000,
    value=100000,
    step=10000
)

# Strategy-specific parameters
st.sidebar.markdown("### Strategy Parameters")

if strategy_type == "SMA Crossover":
    short_window = st.sidebar.slider("Short Window", 10, 100, 50, 5)
    long_window = st.sidebar.slider("Long Window", 100, 300, 200, 10)
    strategy = SMACrossoverStrategy(short_window=short_window, long_window=long_window)
    
elif strategy_type == "RSI":
    rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14, 1)
    oversold = st.sidebar.slider("Oversold Threshold", 20, 40, 30, 5)
    overbought = st.sidebar.slider("Overbought Threshold", 60, 80, 70, 5)
    strategy = RSIStrategy(period=rsi_period, oversold=oversold, overbought=overbought)
    
else:  # MACD
    fast_period = st.sidebar.slider("Fast Period", 8, 20, 12, 1)
    slow_period = st.sidebar.slider("Slow Period", 20, 35, 26, 1)
    signal_period = st.sidebar.slider("Signal Period", 5, 15, 9, 1)
    strategy = MACDStrategy(fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)

# Trading Costs
with st.sidebar.expander("Advanced Settings"):
    commission = st.number_input("Commission Rate", 0.0, 0.01, 0.001, 0.0001, format="%.4f")
    slippage = st.number_input("Slippage Rate", 0.0, 0.01, 0.0005, 0.0001, format="%.4f")

# Run Backtest Button
run_backtest = st.sidebar.button("🚀 Run Backtest", type="primary", use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 About")
st.sidebar.info(
    "This platform allows you to backtest trading strategies "
    "on historical stock data and analyze performance metrics."
)

# Main Content Area
if run_backtest:
    with st.spinner(f'Running backtest for {symbol}...'):
        try:
            # Create and run backtest
            engine = BacktestEngine(
                strategy=strategy,
                symbol=symbol,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage
            )
            
            results = engine.run()
            
            if not results or not results.get('metrics'):
                st.error("❌ No results generated. The strategy may not have produced any trades.")
                st.stop()
            
            metrics = results['metrics']
            equity_curve = results['equity_curve']
            trades = results['trades']
            
            # Display Results
            st.success(f"✅ Backtest completed for {symbol}")
            
            # Key Metrics Row
            st.markdown("### 📊 Performance Metrics")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "Total Return",
                    f"{metrics['total_return_pct']:.2f}%",
                    delta=f"${metrics['final_value'] - metrics['initial_capital']:,.0f}"
                )
            
            with col2:
                st.metric(
                    "Sharpe Ratio",
                    f"{metrics['sharpe_ratio']:.3f}",
                    delta="Good" if metrics['sharpe_ratio'] > 1 else "Poor"
                )
            
            with col3:
                st.metric(
                    "Max Drawdown",
                    f"{metrics['max_drawdown_pct']:.2f}%",
                    delta="High Risk" if metrics['max_drawdown_pct'] > 20 else "Low Risk",
                    delta_color="inverse"
                )
            
            with col4:
                st.metric(
                    "Win Rate",
                    f"{metrics['win_rate_pct']:.1f}%",
                    delta=f"{metrics['winning_trades']}/{metrics['total_trades']} wins"
                )
            
            with col5:
                st.metric(
                    "Profit Factor",
                    f"{metrics['profit_factor']:.2f}",
                    delta="Good" if metrics['profit_factor'] > 1.5 else "Poor"
                )
            
            # Charts
            st.markdown("### 📈 Performance Charts")
            
            # Equity Curve Chart
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Portfolio Value Over Time', 'Drawdown'),
                vertical_spacing=0.12,
                row_heights=[0.7, 0.3]
            )
            
            # Portfolio value
            fig.add_trace(
                go.Scatter(
                    x=equity_curve.index,
                    y=equity_curve.values,
                    name='Portfolio Value',
                    line=dict(color='#00D9FF', width=2)
                ),
                row=1, col=1
            )
            
            # Initial capital line
            fig.add_hline(
                y=initial_capital,
                line_dash="dash",
                line_color="red",
                annotation_text="Initial Capital",
                row=1, col=1
            )
            
            # Drawdown
            cumulative_max = equity_curve.expanding().max()
            drawdown = (equity_curve - cumulative_max) / cumulative_max * 100
            
            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values,
                    name='Drawdown',
                    fill='tozeroy',
                    line=dict(color='#FF4B4B', width=1)
                ),
                row=2, col=1
            )
            
            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Value ($)", row=1, col=1)
            fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
            
            fig.update_layout(
                height=600,
                showlegend=True,
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade Statistics
            st.markdown("### 💼 Trade Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Summary")
                summary_df = pd.DataFrame({
                    'Metric': [
                        'Total Trades',
                        'Winning Trades',
                        'Losing Trades',
                        'Average Profit',
                        'Average Win',
                        'Average Loss'
                    ],
                    'Value': [
                        metrics['total_trades'],
                        metrics['winning_trades'],
                        metrics['losing_trades'],
                        f"${metrics['avg_profit']:.2f}",
                        f"${metrics['avg_win']:.2f}",
                        f"${metrics['avg_loss']:.2f}"
                    ]
                })
                st.dataframe(summary_df, hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown("#### Returns Distribution")
                if trades:
                    profits = [t['profit'] for t in trades]
                    fig_hist = go.Figure(data=[go.Histogram(
                        x=profits,
                        nbinsx=20,
                        marker_color='#00D9FF'
                    )])
                    fig_hist.update_layout(
                        xaxis_title="Profit/Loss ($)",
                        yaxis_title="Frequency",
                        showlegend=False,
                        height=300,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
            
            # Trade History
            if trades:
                st.markdown("### 📋 Trade History")
                trades_df = pd.DataFrame(trades)
                trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.date
                trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.date
                
                # Format columns
                trades_df['entry_price'] = trades_df['entry_price'].apply(lambda x: f"${x:.2f}")
                trades_df['exit_price'] = trades_df['exit_price'].apply(lambda x: f"${x:.2f}")
                trades_df['profit'] = trades_df['profit'].apply(lambda x: f"${x:.2f}")
                trades_df['profit_pct'] = trades_df['profit_pct'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(
                    trades_df,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "entry_date": "Entry Date",
                        "exit_date": "Exit Date",
                        "entry_price": "Entry Price",
                        "exit_price": "Exit Price",
                        "shares": "Shares",
                        "profit": "Profit",
                        "profit_pct": "Return %",
                        "duration": "Duration (days)"
                    }
                )
                
                # Download button for trade history
                csv = trades_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Trade History",
                    data=csv,
                    file_name=f"{symbol}_{strategy_type}_trades.csv",
                    mime="text/csv"
                )
            
        except Exception as e:
            st.error(f"❌ Error running backtest: {str(e)}")
            st.exception(e)

else:
    # Welcome Screen
    st.markdown("""
    ## 👋 Welcome to the Algorithmic Trading Platform
    
    This application allows you to backtest trading strategies on historical stock data.
    
    ### 🚀 Getting Started
    
    1. **Select a strategy** from the sidebar (SMA Crossover, RSI, or MACD)
    2. **Enter a stock symbol** (e.g., AAPL, TSLA, MSFT)
    3. **Choose date range** for backtesting
    4. **Adjust parameters** for your selected strategy
    5. **Click "Run Backtest"** to see results
    
    ### 📊 Available Strategies
    
    - **SMA Crossover**: Trend-following strategy using moving averages
    - **RSI**: Mean reversion strategy using Relative Strength Index
    - **MACD**: Combines trend and momentum indicators
    
    ### 💡 Tips
    
    - Use at least 1 year of data for reliable results
    - Sharpe Ratio > 1.0 indicates good risk-adjusted returns
    - Win Rate > 50% is generally positive
    - Lower drawdown indicates better risk management
    
    ---
    
    **Ready to start?** Configure your strategy in the sidebar and click "Run Backtest"!
    """)
    
    # Sample results preview
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📈 **Backtest** historical strategies")
    with col2:
        st.info("📊 **Analyze** performance metrics")
    with col3:
        st.info("💰 **Optimize** trading parameters")
