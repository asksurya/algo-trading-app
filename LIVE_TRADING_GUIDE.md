# 🤖 Live Trading Guide

## Overview

The Live Trading feature automatically evaluates strategies on your selected stocks, identifies the best strategy for each stock, and executes trades via Alpaca API.

## How It Works

### 1. Strategy Evaluation
- **Runs backtests** on all selected strategies for each stock
- **Compares performance** using metrics like Sharpe ratio, returns, profit factor
- **Selects best strategy** for each stock automatically
- **Uses 1 year** of historical data by default (configurable)

### 2. Signal Generation
- **Monitors selected stocks** at regular intervals (default: 5 minutes)
- **Generates signals** using the best strategy for each stock
- **Respects risk limits** (position size, max positions, etc.)

### 3. Trade Execution
- **Automatically executes trades** when signals are generated
- **Paper trading** available to test without real money
- **Live trading** available once you're confident

## Setup Instructions

### Step 1: Configure Alpaca Account

1. **Create Alpaca Account**:
   - Go to [https://alpaca.markets](https://alpaca.markets)
   - Sign up for a free account
   - Get your API keys (Paper Trading and/or Live Trading)

2. **Add API Keys**:
   Edit `config/alpaca_config.py`:
   ```python
   ALPACA_API_KEY = "your_api_key_here"
   ALPACA_SECRET_KEY = "your_secret_key_here"
   ```

3. **Fund Your Account** (for live trading):
   - Paper trading: Already funded with $100,000 virtual money
   - Live trading: Deposit real money (minimum $500 recommended)

### Step 2: Access Live Trading

1. **Run the App**:
   ```bash
   streamlit run app.py
   ```

2. **Navigate to Live Trading**:
   - Look for "Live Trading" in the Streamlit sidebar pages
   - Or go directly to `http://localhost:8501/live_trading`

### Step 3: Evaluate Strategies

1. **Select Your Stocks**:
   ```
   AAPL
   MSFT
   TSLA
   NVDA
   AMD
   ```

2. **Choose Strategies to Evaluate**:
   - SMA Crossover
   - RSI
   - MACD
   - Bollinger Bands
   - Momentum
   - Mean Reversion
   - Breakout
   - VWAP
   - Pairs Trading
   - ML Strategy

3. **Set Risk Parameters**:
   - Initial Capital: $500 (or your account balance)
   - Risk Per Trade: 2% (recommended 1-5%)
   - Max Positions: 5 (don't overextend)

4. **Click "Evaluate Strategies"**:
   - System runs backtests on all strategy/stock combinations
   - Identifies best strategy for each stock
   - Shows results table

### Step 4: Start Trading

1. **Review Best Strategies**:
   - Check which strategy was selected for each stock
   - View performance metrics (Sharpe ratio, returns, etc.)

2. **Choose Trading Mode**:
   - **Paper Trading**: Test with virtual money (RECOMMENDED FIRST)
   - **Live Trading**: Use real money (only after testing)

3. **Start Automated Trading**:
   - Click "Start Auto Trading"
   - System will:
     - Check for signals every N seconds (configurable)
     - Execute trades automatically
     - Monitor positions
     - Close positions when sell signals occur

4. **Monitor Your Portfolio**:
   - View real-time portfolio value
   - See current positions
   - Track unrealized P&L
   - Monitor executed trades

## Example Workflow

### Your $500 Paper Trading Test

1. **Start with Paper Trading**:
   ```
   Mode: Paper Trading
   Stocks: AAPL, MSFT, TSLA, NVDA, AMD
   Strategies: All 10 strategies
   Initial Capital: $500
   Risk Per Trade: 2%
   Max Positions: 5
   ```

2. **Evaluate**:
   - Click "Evaluate Strategies"
   - Wait 2-3 minutes for backtests to complete
   - Review results:
     ```
     AAPL -> Best: RSI (Sharpe: 1.85)
     MSFT -> Best: SMA Crossover (Sharpe: 1.92)
     TSLA -> Best: Momentum (Sharpe: 2.1)
     NVDA -> Best: ML Strategy (Sharpe: 2.3)
     AMD -> Best: MACD (Sharpe: 1.75)
     ```

3. **Start Trading**:
   - Click "Start Auto Trading"
   - System begins monitoring
   - Current signals shown:
     ```
     AAPL: BUY (using RSI)
     MSFT: HOLD (using SMA Crossover)
     TSLA: HOLD (using Momentum)
     NVDA: BUY (using ML Strategy)
     AMD: SELL (using MACD)
     ```

4. **Trades Execute**:
   - AAPL: BUY 5 shares @ $225 = $1,125 (needs $10 in account)
   - NVDA: BUY 1 share @ $140 = $140 (needs $10 in account)
   - System respects 2% risk limit per trade

5. **Monitor**:
   - Check portfolio tab regularly
   - View unrealized P&L
   - Wait for sell signals

6. **Test for 1-2 Weeks**:
   - Let it run in paper trading
   - Monitor performance
   - Adjust parameters if needed

7. **Switch to Live** (only if satisfied):
   - Change mode to "Live Trading"
   - Deposit $500 in Alpaca account
   - Start auto trading with real money

## Risk Management

### Position Sizing
- **Risk Per Trade**: 2% means each trade risks 2% of capital
- **Max Positions**: 5 means max 5 stocks at once
- **Total Risk**: Maximum 10% at risk (5 positions × 2% each)

### Stop Loss
- Strategies include exit signals
- System automatically closes positions on sell signals
- Manual override available in Alpaca dashboard

### Diversification
- Trade multiple stocks across sectors
- Use different strategies for different stocks
- Don't concentrate in one sector

## Important Warnings

### ⚠️ Before Live Trading

1. **Test First**: Always use paper trading for at least 1-2 weeks
2. **Start Small**: Begin with minimum capital ($500)
3. **Monitor Daily**: Check positions and P&L daily
4. **Set Limits**: Use conservative risk settings (1-2% per trade)
5. **Understand Strategies**: Know how each strategy works
6. **Check Market Hours**: Trading only during market hours (9:30 AM - 4:00 PM ET)

### 🚫 Common Mistakes to Avoid

1. **Over-leverage**: Don't risk >5% per trade
2. **Too many positions**: Start with 3-5 max
3. **No monitoring**: Check daily, don't set and forget
4. **Ignoring signals**: Trust the strategy or don't use it
5. **Emotional trading**: Let the system work, don't override
6. **Insufficient testing**: Paper trade first!

## Troubleshooting

### "Could not connect to Alpaca"
- Check API keys in `config/alpaca_config.py`
- Verify internet connection
- Check Alpaca service status

### "No trades executing"
- Verify you're in market hours
- Check if signals are being generated
- Ensure you have available cash
- Check position limits

### "Strategy evaluation failed"
- Check if stocks are valid symbols
- Verify historical data is available
- Try with fewer stocks/strategies

## Performance Monitoring

### Key Metrics to Watch

1. **Portfolio Value**: Total account value
2. **Unrealized P&L**: Current profit/loss on open positions
3. **Win Rate**: % of profitable trades
4. **Sharpe Ratio**: Risk-adjusted returns
5. **Max Drawdown**: Largest peak-to-trough decline

### When to Adjust

- **Poor performance**: Try different strategies or stocks
- **High volatility**: Reduce position size
- **Consistent losses**: Stop and reassess
- **Market change**: Re-evaluate strategies quarterly

## Advanced Features

### Custom Check Intervals
```python
# Check signals every 5 minutes
check_interval = 300

# Check signals every hour
check_interval = 3600
```

### Multiple Optimization Metrics
- **Sharpe Ratio**: Risk-adjusted returns (default)
- **Total Return**: Absolute returns
- **Profit Factor**: Ratio of wins to losses

### Programmatic Trading

Run live trading from command line:
```python
from src.trading.live_trader import LiveTrader
from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy

strategies = {
    'SMA': SMACrossoverStrategy(),
    'RSI': RSIStrategy()
}

trader = LiveTrader(
    strategies=strategies,
    symbols=['AAPL', 'MSFT'],
    initial_capital=500,
    paper_trading=True
)

# Evaluate
results = trader.evaluate_strategies()

# Start live trading loop
trader.run_live_trading(check_interval=300)
```

## Support

For issues or questions:
1. Check this guide
2. Review strategy documentation in `STRATEGIES_GUIDE.md`
3. Check Alpaca API documentation
4. Report bugs in the app

## Disclaimer

**This software is for educational purposes only. Trading involves significant risk of loss. Past performance does not guarantee future results. Always test thoroughly with paper trading before using real money. The developers are not responsible for any financial losses.**
