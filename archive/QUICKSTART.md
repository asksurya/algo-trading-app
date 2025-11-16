# Quick Start Guide

## Installation

1. **Install Python dependencies:**
```bash
cd algo-trading-app
pip install -r requirements.txt
```

2. **Configure API Keys (Optional for backtesting):**
   
   Edit `config/alpaca_config.py` and add your Alpaca API credentials:
   ```python
   ALPACA_API_KEY = "your_actual_api_key"
   ALPACA_SECRET_KEY = "your_actual_secret_key"
   ```
   
   **Note:** For backtesting only, you don't need Alpaca keys. The app will automatically use Yahoo Finance as a fallback.

## Running Your First Backtest

**Basic backtest with default parameters:**
```bash
python main.py backtest --strategy sma --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01
```

**Backtest with visualization:**
```bash
python main.py backtest --strategy sma --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01 --plot
```

**Backtest RSI strategy:**
```bash
python main.py backtest --strategy rsi --symbol TSLA --start-date 2023-01-01 --end-date 2024-01-01 --plot
```

**Custom SMA parameters:**
```bash
python main.py backtest --strategy sma --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01 --short-window 20 --long-window 50
```

## Compare Multiple Strategies

```bash
python main.py compare --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01 --plot
```

## Paper Trading (Requires Alpaca API Keys)

**Start paper trading:**
```bash
python main.py live --strategy sma --symbols AAPL,TSLA --paper
```

**Note:** Press `Ctrl+C` to stop the trader gracefully.

## Understanding the Output

### Backtest Results Include:
- **Total Return**: Overall percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profits / Gross losses

### Good Strategy Benchmarks:
- Sharpe Ratio > 1.0 (Good), > 2.0 (Excellent)
- Win Rate > 50%
- Profit Factor > 1.5
- Max Drawdown < 20%

## Troubleshooting

### "No data available for backtesting"
- The app automatically falls back to Yahoo Finance if Alpaca fails
- Ensure you have internet connection
- Try a different date range

### "Matplotlib not installed"
- Install with: `pip install matplotlib seaborn`

### "401 Authorization Required" (Alpaca)
- This is normal if you haven't configured API keys
- The app will automatically use Yahoo Finance instead
- Configure keys in `config/alpaca_config.py` for live trading

## Next Steps

1. **Test the setup:**
   ```bash
   python test_setup.py
   ```

2. **Create your own strategy:**
   - Copy `src/strategies/sma_crossover.py`
   - Modify the `generate_signals()` method
   - Add your strategy to `main.py`

3. **Optimize parameters:**
   - Run backtests with different parameter combinations
   - Compare results to find optimal settings

4. **Paper trade:**
   - Test your strategy in real-time without risk
   - Monitor performance before going live

## Safety Notes

⚠️ **IMPORTANT:**
- Always paper trade first before using real money
- Never risk more than you can afford to lose
- Past performance does not guarantee future results
- This is educational software - use at your own risk

## Getting Help

- Check `README.md` for detailed documentation
- Review code comments for implementation details
- Test with small amounts first when paper trading
