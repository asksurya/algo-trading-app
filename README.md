# Algorithmic Trading Application

A Python-based algorithmic trading platform with backtesting, live trading via Alpaca API, and visualization capabilities.

## Features

- **Backtesting Engine**: Test trading strategies on historical data
- **Live Trading**: Execute trades via Alpaca API (paper and live trading)
- **Strategy Framework**: Built-in example strategies (SMA crossover, RSI, etc.)
- **Data Management**: Fetch and store historical market data
- **Visualization**: Charts for performance analysis and trade signals
- **Risk Management**: Position sizing, stop-loss, and portfolio limits
- **Portfolio Tracking**: Real-time portfolio monitoring and metrics

## Project Structure

```
algo-trading-app/
├── config/
│   ├── config.yaml           # Main configuration
│   └── alpaca_config.py      # Alpaca API credentials
├── src/
│   ├── data/
│   │   ├── data_fetcher.py   # Historical data fetching
│   │   └── data_manager.py   # Data storage and management
│   ├── strategies/
│   │   ├── base_strategy.py  # Base strategy class
│   │   ├── sma_crossover.py  # SMA crossover strategy
│   │   └── rsi_strategy.py   # RSI-based strategy
│   ├── backtesting/
│   │   ├── backtest_engine.py # Backtesting logic
│   │   └── performance.py     # Performance metrics
│   ├── trading/
│   │   ├── trader.py          # Live trading executor
│   │   └── order_manager.py   # Order management
│   ├── risk/
│   │   └── risk_manager.py    # Risk management
│   └── visualization/
│       └── plotter.py         # Charting and visualization
├── data/                      # Historical data storage
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
└── main.py                    # Main application entry point
```

## Installation

1. Clone or navigate to the project directory
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure Alpaca API credentials in `config/alpaca_config.py`:
```python
ALPACA_API_KEY = "your_api_key"
ALPACA_SECRET_KEY = "your_secret_key"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading
```

## Usage

### Backtesting a Strategy

```python
from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.sma_crossover import SMACrossoverStrategy

# Initialize strategy
strategy = SMACrossoverStrategy(short_window=50, long_window=200)

# Run backtest
engine = BacktestEngine(
    strategy=strategy,
    symbol='AAPL',
    start_date='2023-01-01',
    end_date='2024-01-01',
    initial_capital=100000
)

results = engine.run()
engine.plot_results()
```

### Live Trading

```python
from src.trading.trader import LiveTrader
from src.strategies.sma_crossover import SMACrossoverStrategy

# Initialize strategy and trader
strategy = SMACrossoverStrategy(short_window=50, long_window=200)
trader = LiveTrader(strategy=strategy, symbols=['AAPL', 'TSLA'])

# Start live trading (paper trading by default)
trader.start()
```

### Main Application

```bash
# Run backtest
python main.py --mode backtest --strategy sma --symbol AAPL --start 2023-01-01 --end 2024-01-01

# Run live trading
python main.py --mode live --strategy sma --symbols AAPL TSLA GOOGL
```

## Available Strategies

1. **SMA Crossover**: Moving average crossover strategy
   - Buy when short MA crosses above long MA
   - Sell when short MA crosses below long MA

2. **RSI Strategy**: Relative Strength Index-based strategy
   - Buy when RSI < 30 (oversold)
   - Sell when RSI > 70 (overbought)

## Configuration

Edit `config/config.yaml` to customize:
- Default trading parameters
- Risk management settings
- Position sizing rules
- Logging preferences

## Safety Notes

- **Always start with paper trading** (Alpaca paper API)
- Test strategies thoroughly with backtesting before live trading
- Set appropriate risk limits and position sizes
- Monitor your trades regularly
- Never risk more than you can afford to lose

## API Keys

Get your free Alpaca API keys at: https://alpaca.markets/
- Paper trading is free and perfect for testing
- Live trading requires account funding

## 🚀 Deployment

### Deploy to Cloud (5 minutes):
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

**Quick Deploy to Streamlit Cloud (Free):**
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo and deploy
4. Access on any device including iPhone! 📱

**Docker Deployment:**
```bash
docker build -t algo-trading-app .
docker run -p 8501:8501 algo-trading-app
```

### Mobile Access
✅ Already mobile-responsive! Works perfectly on iPhone/Android
✅ Add to home screen for app-like experience

## License

MIT License - Use at your own risk. Not financial advice.
