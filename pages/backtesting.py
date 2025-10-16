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
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.breakout_strategy import BreakoutStrategy
from src.strategies.vwap_strategy import VWAPStrategy
from src.strategies.pairs_trading import PairsTradingStrategy
from src.strategies.ml_strategy import MLStrategy
from src.strategies.adaptive_ml_strategy import AdaptiveMLStrategy
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

# Mode Selection
mode = st.sidebar.radio(
    "Mode",
    ["Single Strategy", "Compare Strategies"],
    help="Choose between testing one strategy or comparing multiple"
)

# Strategy Selection
if mode == "Single Strategy":
    strategy_type = st.sidebar.selectbox(
        "Select Strategy",
        ["SMA Crossover", "RSI", "MACD", "Bollinger Bands", "Momentum", "Mean Reversion", "Breakout", "VWAP", "Pairs Trading", "ML Strategy", "Adaptive ML"],
        help="Choose a trading strategy to backtest"
    )
else:
    strategies_to_compare = st.sidebar.multiselect(
        "Select Strategies to Compare",
        ["SMA Crossover", "RSI", "MACD", "Bollinger Bands", "Momentum", "Mean Reversion", "Breakout", "VWAP", "Pairs Trading", "ML Strategy", "Adaptive ML"],
        default=["SMA Crossover", "RSI", "MACD"],
        help="Choose multiple strategies to compare"
    )

# Symbol Input
if mode == "Compare Strategies":
    # Allow multiple symbols in comparison mode
    symbols_input = st.sidebar.text_input(
        "Stock Symbols (comma-separated)",
        value="AAPL",
        help="Enter one or more stock ticker symbols separated by commas (e.g., AAPL, MSFT, TSLA)"
    )
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
else:
    # Single symbol for single strategy mode
    symbol = st.sidebar.text_input(
        "Stock Symbol",
        value="AAPL",
        help="Enter a valid stock ticker symbol"
    ).upper()
    symbols = [symbol]

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

def create_strategy(strategy_name, show_params=True):
    """Create strategy instance based on name."""
    if strategy_name == "SMA Crossover":
        if show_params:
            short_window = st.sidebar.slider("Short Window", 10, 100, 50, 5)
            long_window = st.sidebar.slider("Long Window", 100, 300, 200, 10)
        else:
            short_window, long_window = 50, 200
        return SMACrossoverStrategy(short_window=short_window, long_window=long_window)
    
    elif strategy_name == "RSI":
        if show_params:
            rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14, 1)
            oversold = st.sidebar.slider("Oversold Threshold", 20, 40, 30, 5)
            overbought = st.sidebar.slider("Overbought Threshold", 60, 80, 70, 5)
        else:
            rsi_period, oversold, overbought = 14, 30, 70
        return RSIStrategy(period=rsi_period, oversold=oversold, overbought=overbought)
    
    elif strategy_name == "MACD":
        if show_params:
            fast_period = st.sidebar.slider("Fast Period", 8, 20, 12, 1)
            slow_period = st.sidebar.slider("Slow Period", 20, 35, 26, 1)
            signal_period = st.sidebar.slider("Signal Period", 5, 15, 9, 1)
        else:
            fast_period, slow_period, signal_period = 12, 26, 9
        return MACDStrategy(fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
    
    elif strategy_name == "Bollinger Bands":
        if show_params:
            bb_period = st.sidebar.slider("Period", 10, 50, 20, 5)
            num_std = st.sidebar.slider("Std Deviations", 1.0, 3.0, 2.0, 0.5)
        else:
            bb_period, num_std = 20, 2.0
        return BollingerBandsStrategy(period=bb_period, num_std=num_std)
    
    elif strategy_name == "Momentum":
        if show_params:
            mom_period = st.sidebar.slider("Momentum Period", 10, 50, 20, 5)
            threshold = st.sidebar.slider("Threshold", 0.0, 5.0, 0.0, 0.5)
        else:
            mom_period, threshold = 20, 0.0
        return MomentumStrategy(period=mom_period, threshold=threshold)
    
    elif strategy_name == "Mean Reversion":
        if show_params:
            mr_period = st.sidebar.slider("Period", 10, 50, 20, 5)
            entry_z = st.sidebar.slider("Entry Z-Score", 1.0, 3.0, 2.0, 0.5)
            exit_z = st.sidebar.slider("Exit Z-Score", 0.0, 1.5, 0.5, 0.25)
        else:
            mr_period, entry_z, exit_z = 20, 2.0, 0.5
        return MeanReversionStrategy(period=mr_period, entry_threshold=entry_z, exit_threshold=exit_z)
    
    elif strategy_name == "Breakout":
        if show_params:
            lookback = st.sidebar.slider("Lookback Period", 10, 100, 20, 5)
            breakout_pct = st.sidebar.slider("Breakout Threshold %", 0.5, 5.0, 2.0, 0.5) / 100
        else:
            lookback, breakout_pct = 20, 0.02
        return BreakoutStrategy(lookback_period=lookback, breakout_threshold=breakout_pct)
    
    elif strategy_name == "VWAP":
        if show_params:
            vwap_period = st.sidebar.slider("VWAP Period", 10, 50, 20, 5)
        else:
            vwap_period = 20
        return VWAPStrategy(period=vwap_period)
    
    elif strategy_name == "Pairs Trading":
        if show_params:
            pairs_period = st.sidebar.slider("Period", 20, 60, 30, 5)
            entry_z = st.sidebar.slider("Entry Z-Score", 1.5, 3.0, 2.0, 0.25)
            exit_z = st.sidebar.slider("Exit Z-Score", 0.25, 1.5, 0.5, 0.25)
        else:
            pairs_period, entry_z, exit_z = 30, 2.0, 0.5
        return PairsTradingStrategy(period=pairs_period, entry_z_score=entry_z, exit_z_score=exit_z)
    
    elif strategy_name == "ML Strategy":
        if show_params:
            ml_short = st.sidebar.slider("Short Period", 5, 20, 10, 5)
            ml_long = st.sidebar.slider("Long Period", 20, 50, 30, 5)
            ml_threshold = st.sidebar.slider("Confidence Threshold", 0.3, 0.9, 0.6, 0.1)
        else:
            ml_short, ml_long, ml_threshold = 10, 30, 0.6
        return MLStrategy(short_period=ml_short, long_period=ml_long, threshold=ml_threshold)
    
    elif strategy_name == "Adaptive ML":
        if show_params:
            ada_confidence = st.sidebar.slider("Confidence Threshold", 0.5, 0.9, 0.6, 0.05)
            ada_sentiment = st.sidebar.checkbox("Use Sentiment Analysis", value=False, 
                help="Enable sentiment analysis (requires API keys in config/sentiment_config.py)")
        else:
            ada_confidence, ada_sentiment = 0.6, False
        return AdaptiveMLStrategy(confidence_threshold=ada_confidence, use_sentiment=ada_sentiment)

if mode == "Single Strategy":
    strategy = create_strategy(strategy_type, show_params=True)
else:
    # In comparison mode, use default parameters
    strategies = {name: create_strategy(name, show_params=False) for name in strategies_to_compare}

# Trading Costs
with st.sidebar.expander("Advanced Settings"):
    commission = st.number_input("Commission Rate", 0.0, 0.01, 0.001, 0.0001, format="%.4f")
    slippage = st.number_input("Slippage Rate", 0.0, 0.01, 0.0005, 0.0001, format="%.4f")

# Run Backtest Button
run_backtest = st.sidebar.button("🚀 Run Backtest", type="primary", width="stretch")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 About")
st.sidebar.info(
    "This platform allows you to backtest trading strategies "
    "on historical stock data and analyze performance metrics."
)

# Main Content Area
if run_backtest:
    if mode == "Compare Strategies":
        # Comparison Mode
        if not strategies_to_compare or len(strategies_to_compare) < 2:
            st.warning("⚠️ Please select at least 2 strategies to compare.")
            st.stop()
        
        if len(symbols) == 0:
            st.error("❌ Please enter at least one valid stock symbol.")
            st.stop()
        
        with st.spinner(f'Running backtests for {len(strategies_to_compare)} strategies on {len(symbols)} stock(s)...'):
            try:
                all_results = {}
                
                # Run backtest for each strategy on each symbol
                for symbol in symbols:
                    for strategy_name in strategies_to_compare:
                        strategy_obj = strategies[strategy_name]
                        engine = BacktestEngine(
                            strategy=strategy_obj,
                            symbol=symbol,
                            start_date=start_date.strftime('%Y-%m-%d'),
                            end_date=end_date.strftime('%Y-%m-%d'),
                            initial_capital=initial_capital,
                            commission=commission,
                            slippage=slippage
                        )
                        results = engine.run()
                        
                        # Store results with combined key
                        key = f"{strategy_name} ({symbol})" if len(symbols) > 1 else strategy_name
                        if results and results.get('metrics'):
                            all_results[key] = results
                
                if not all_results:
                    st.error("❌ No valid results generated for any strategy.")
                    st.stop()
                
                if len(symbols) == 1:
                    st.success(f"✅ Comparison completed for {len(strategies_to_compare)} strategies on {symbols[0]}")
                else:
                    st.success(f"✅ Comparison completed for {len(strategies_to_compare)} strategies across {len(symbols)} stocks")
                
                # Comparison Table
                st.markdown("### 📊 Strategy Comparison")
                
                comparison_data = []
                for strategy_name, results in all_results.items():
                    metrics = results['metrics']
                    comparison_data.append({
                        'Strategy': strategy_name,
                        'Return %': metrics['total_return_pct'],
                        'Sharpe': metrics['sharpe_ratio'],
                        'Max DD %': metrics['max_drawdown_pct'],
                        'Win Rate %': metrics['win_rate_pct'],
                        'Profit Factor': metrics['profit_factor'],
                        'Trades': metrics['total_trades'],
                        'Final Value $': metrics['final_value']
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # Sort by Return % descending by default
                comparison_df = comparison_df.sort_values('Return %', ascending=False)
                
                # Display with custom column configuration for better formatting
                st.dataframe(
                    comparison_df,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Strategy": st.column_config.TextColumn("Strategy", width="medium"),
                        "Return %": st.column_config.NumberColumn("Return %", format="%.2f", help="Total return percentage"),
                        "Sharpe": st.column_config.NumberColumn("Sharpe Ratio", format="%.3f", help="Risk-adjusted return"),
                        "Max DD %": st.column_config.NumberColumn("Max Drawdown %", format="%.2f", help="Maximum drawdown"),
                        "Win Rate %": st.column_config.NumberColumn("Win Rate %", format="%.1f", help="Percentage of winning trades"),
                        "Profit Factor": st.column_config.NumberColumn("Profit Factor", format="%.2f", help="Gross profit / Gross loss"),
                        "Trades": st.column_config.NumberColumn("Total Trades", help="Number of trades executed"),
                        "Final Value $": st.column_config.NumberColumn("Final Value", format="$%,.0f", help="Final portfolio value")
                    }
                )
                
                # Add download button for comparison results
                csv = comparison_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Comparison Results",
                    data=csv,
                    file_name=f"strategy_comparison_{'-'.join(symbols)}.csv",
                    mime="text/csv"
                )
                
                # Equity Curves Comparison
                st.markdown("### 📈 Equity Curves Comparison")
                fig = go.Figure()
                
                colors = ['#00D9FF', '#FF4B4B', '#00FF00', '#FFA500', '#9370DB', '#FFD700', '#FF69B4', '#FF1493', '#00CED1', '#FFD700']
                
                for idx, (strategy_name, results) in enumerate(all_results.items()):
                    equity_curve = results['equity_curve']
                    fig.add_trace(go.Scatter(
                        x=equity_curve.index,
                        y=equity_curve.values,
                        name=strategy_name,
                        line=dict(color=colors[idx % len(colors)], width=2)
                    ))
                
                fig.add_hline(
                    y=initial_capital,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text="Initial Capital"
                )
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Portfolio Value ($)",
                    hovermode='x unified',
                    template='plotly_white',
                    height=500
                )
                
                st.plotly_chart(fig, width="stretch")
                
                # Performance Metrics Comparison Charts
                st.markdown("### 📊 Performance Metrics Comparison")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Returns comparison
                    fig_returns = go.Figure(data=[
                        go.Bar(
                            x=[name for name in all_results.keys()],
                            y=[all_results[name]['metrics']['total_return_pct'] for name in all_results.keys()],
                            marker_color='#00D9FF'
                        )
                    ])
                    fig_returns.update_layout(
                        title="Total Return %",
                        xaxis_title="Strategy",
                        yaxis_title="Return %",
                        template='plotly_white',
                        height=350
                    )
                    st.plotly_chart(fig_returns, width="stretch")
                
                with col2:
                    # Sharpe Ratio comparison
                    fig_sharpe = go.Figure(data=[
                        go.Bar(
                            x=[name for name in all_results.keys()],
                            y=[all_results[name]['metrics']['sharpe_ratio'] for name in all_results.keys()],
                            marker_color='#FF4B4B'
                        )
                    ])
                    fig_sharpe.update_layout(
                        title="Sharpe Ratio",
                        xaxis_title="Strategy",
                        yaxis_title="Sharpe Ratio",
                        template='plotly_white',
                        height=350
                    )
                    st.plotly_chart(fig_sharpe, width="stretch")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    # Win Rate comparison
                    fig_winrate = go.Figure(data=[
                        go.Bar(
                            x=[name for name in all_results.keys()],
                            y=[all_results[name]['metrics']['win_rate_pct'] for name in all_results.keys()],
                            marker_color='#00FF00'
                        )
                    ])
                    fig_winrate.update_layout(
                        title="Win Rate %",
                        xaxis_title="Strategy",
                        yaxis_title="Win Rate %",
                        template='plotly_white',
                        height=350
                    )
                    st.plotly_chart(fig_winrate, width="stretch")
                
                with col4:
                    # Max Drawdown comparison
                    fig_dd = go.Figure(data=[
                        go.Bar(
                            x=[name for name in all_results.keys()],
                            y=[all_results[name]['metrics']['max_drawdown_pct'] for name in all_results.keys()],
                            marker_color='#FFA500'
                        )
                    ])
                    fig_dd.update_layout(
                        title="Max Drawdown %",
                        xaxis_title="Strategy",
                        yaxis_title="Drawdown %",
                        template='plotly_white',
                        height=350
                    )
                    st.plotly_chart(fig_dd, width="stretch")
                
                # Best Strategy Recommendation
                st.markdown("### 🏆 Best Strategy Analysis")
                
                # Calculate best strategies for different metrics
                best_return = max(all_results.items(), key=lambda x: x[1]['metrics']['total_return_pct'])
                best_sharpe = max(all_results.items(), key=lambda x: x[1]['metrics']['sharpe_ratio'])
                best_winrate = max(all_results.items(), key=lambda x: x[1]['metrics']['win_rate_pct'])
                lowest_dd = min(all_results.items(), key=lambda x: x[1]['metrics']['max_drawdown_pct'])
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Highest Return",
                        best_return[0],
                        f"{best_return[1]['metrics']['total_return_pct']:.2f}%"
                    )
                
                with col2:
                    st.metric(
                        "Best Risk-Adjusted",
                        best_sharpe[0],
                        f"Sharpe: {best_sharpe[1]['metrics']['sharpe_ratio']:.3f}"
                    )
                
                with col3:
                    st.metric(
                        "Highest Win Rate",
                        best_winrate[0],
                        f"{best_winrate[1]['metrics']['win_rate_pct']:.1f}%"
                    )
                
                with col4:
                    st.metric(
                        "Lowest Risk",
                        lowest_dd[0],
                        f"DD: {lowest_dd[1]['metrics']['max_drawdown_pct']:.2f}%"
                    )
                
            except Exception as e:
                st.error(f"❌ Error running comparison: {str(e)}")
                st.exception(e)
    
    else:
        # Single Strategy Mode
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
                
                st.plotly_chart(fig, width="stretch")
            
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
                    st.dataframe(summary_df, hide_index=True, width="stretch")
                
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
                        st.plotly_chart(fig_hist, width="stretch")
                
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
                        width="stretch",
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
    
    1. **Choose a mode**: Single Strategy or Compare Strategies
    2. **Select strategy/strategies** from the sidebar
    3. **Enter a stock symbol** (e.g., AAPL, TSLA, MSFT)
    4. **Choose date range** for backtesting
    5. **Adjust parameters** for your selected strategy (single mode)
    6. **Click "Run Backtest"** to see results
    
    ### 📊 Available Strategies
    
    - **SMA Crossover**: Trend-following strategy using moving averages
    - **RSI**: Mean reversion strategy using Relative Strength Index
    - **MACD**: Combines trend and momentum indicators
    - **Bollinger Bands**: Volatility-based mean reversion strategy
    - **Momentum**: Catches strong trends early
    - **Mean Reversion**: Statistical arbitrage using z-scores
    - **Breakout**: Captures breakouts above resistance
    - **VWAP**: Volume-weighted average price for intraday trading
    - **Pairs Trading**: Market neutral statistical arbitrage
    - **ML Strategy**: Ensemble of multiple technical indicators
    
    ### 💡 Tips
    
    - Use at least 1 year of data for reliable results
    - Sharpe Ratio > 1.0 indicates good risk-adjusted returns
    - Win Rate > 50% is generally positive
    - Lower drawdown indicates better risk management
    - Compare multiple strategies to find the best fit for your stock
    
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
