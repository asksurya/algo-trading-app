"""
Diagnostics Page

Debug trading signals and strategy behavior.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys

sys.path.append('..')

from src.data.data_fetcher import DataFetcher
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

st.set_page_config(page_title="Diagnostics", page_icon="🔍", layout="wide")

st.title("🔍 Trading Diagnostics")
st.markdown("Debug your strategies and check why signals might be HOLD")

st.markdown("---")

# Symbol input
symbol = st.text_input("Stock Symbol to Diagnose", value="AAPL").upper()

if st.button("🔍 Run Diagnostics", type="primary"):
    with st.spinner(f"Analyzing {symbol}..."):
        try:
            # Fetch recent data
            fetcher = DataFetcher(data_provider='yahoo')
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)
            
            data = fetcher.fetch_historical_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if data.empty:
                st.error(f"No data available for {symbol}")
                st.stop()
            
            st.success(f"✅ Fetched {len(data)} days of data")
            
            # Show recent data
            st.markdown("### 📊 Recent Price Data")
            st.dataframe(data.tail(10), width="stretch")
            
            st.markdown("---")
            
            # Test each strategy
            st.markdown("### 🎯 Strategy Signal Analysis")
            
            strategies = {
                'SMA Crossover': SMACrossoverStrategy(),
                'RSI': RSIStrategy(),
                'MACD': MACDStrategy(),
                'Bollinger Bands': BollingerBandsStrategy(),
                'Momentum': MomentumStrategy(),
                'Mean Reversion': MeanReversionStrategy(),
                'Breakout': BreakoutStrategy(),
                'VWAP': VWAPStrategy(),
                'Pairs Trading': PairsTradingStrategy(),
                'ML Strategy': MLStrategy(),
                'Adaptive ML': AdaptiveMLStrategy(use_sentiment=False)
            }
            
            for name, strategy in strategies.items():
                st.markdown(f"#### {name}")
                
                try:
                    # Generate signals
                    signals = strategy.generate_signals(data)
                    
                    # Get recent signals
                    recent_signals = signals.tail(10)
                    
                    # Count signals
                    buy_count = (signals == 1).sum()
                    sell_count = (signals == -1).sum()
                    hold_count = (signals == 0).sum()
                    
                    # Current signal
                    current_signal = signals.iloc[-1]
                    if isinstance(current_signal, pd.Series):
                        current_signal = current_signal.iloc[0]
                    
                    signal_str = "🟢 BUY" if current_signal == 1 else "🔴 SELL" if current_signal == -1 else "⚪ HOLD"
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Current Signal", signal_str)
                    with col2:
                        st.metric("Buy Signals (60d)", buy_count)
                    with col3:
                        st.metric("Sell Signals (60d)", sell_count)
                    with col4:
                        st.metric("Hold Signals (60d)", hold_count)
                    
                    # Show recent signals
                    with st.expander(f"View Recent {name} Signals"):
                        signal_df = pd.DataFrame({
                            'Date': recent_signals.index,
                            'Signal': recent_signals.values,
                            'Signal Type': recent_signals.apply(
                                lambda x: "BUY" if x == 1 else "SELL" if x == -1 else "HOLD"
                            )
                        })
                        st.dataframe(signal_df, hide_index=True, width="stretch")
                    
                    # Calculate indicators for this strategy
                    if hasattr(strategy, 'calculate_indicators'):
                        indicators = strategy.calculate_indicators(data)
                        
                        with st.expander(f"View {name} Indicators"):
                            st.dataframe(indicators.tail(10), width="stretch")
                    
                except Exception as e:
                    st.error(f"Error with {name}: {str(e)}")
                    st.exception(e)
                
                st.markdown("---")
            
            # Analysis
            st.markdown("### 💡 Analysis")
            
            if buy_count == 0 and sell_count == 0:
                st.warning("""
                **All signals are HOLD!**
                
                This could mean:
                1. **Market is ranging**: No clear trend, strategies waiting for better setup
                2. **Strategy parameters**: Try adjusting thresholds (RSI: 30/70, SMA: 50/200)
                3. **Time period**: Some strategies need more data to generate signals
                
                **What to do:**
                - Try different stocks (TSLA, AMD, NVDA often have more volatility)
                - Adjust strategy parameters in the main app
                - Wait for market conditions to change
                - Check if it's during market hours (9:30 AM - 4:00 PM ET)
                """)
            else:
                st.info(f"""
                **Strategy is generating signals!**
                
                - Last 60 days: {buy_count} BUY signals, {sell_count} SELL signals
                - If current is HOLD, it's waiting for the right conditions
                - This is normal behavior - strategies don't trade constantly
                """)
        
        except Exception as e:
            st.error(f"Diagnostic error: {str(e)}")
            st.exception(e)

st.markdown("---")
st.markdown("""
### 📚 Understanding HOLD Signals

**HOLD signals are normal and expected!**

Good trading strategies:
- Don't trade constantly
- Wait for high-probability setups
- Preserve capital when conditions aren't favorable

**Why you might see all HOLD:**
1. **Market timing**: Currently no good entry/exit points
2. **Already in position**: Some strategies wait for exit before new entry
3. **Risk management**: Waiting for better risk/reward ratio
4. **Indicator alignment**: Multiple conditions need to align

**What's happening in backtests vs live:**
- **Backtests**: Show the full history with many signals over time
- **Live trading**: Shows current snapshot - might be in HOLD phase

**Try this:**
- Run diagnostics on multiple stocks
- Check during market hours (9:30 AM - 4:00 PM ET)
- Try volatile stocks (TSLA, AMD, NVDA)
- Check back in 30 minutes to see if signals changed
""")
