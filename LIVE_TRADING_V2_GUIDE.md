# Live Trading V2 - Persistent Background Trading System

## Overview

Live Trading V2 is a complete redesign of the trading system that addresses key limitations:

✅ **Runs continuously** - Trading continues even when you close your laptop
✅ **Automatic strategy evaluation** - ALL 11 strategies are tested for each ticker automatically
✅ **Best strategy selection** - System picks the best performing strategy
✅ **Persistent state** - Everything is saved to a database and survives restarts
✅ **Background daemon** - Independent process that runs separately from the UI

## Architecture

### Components

1. **State Manager** (`src/trading/state_manager.py`)
   - SQLite database for persistent storage
   - Stores strategy evaluations, best strategies, trading config, state, and trade history
   - Thread-safe operations

2. **Trading Daemon** (`src/trading/trading_daemon.py`)
   - Background process that runs continuously
   - Monitors trading state and executes trades
   - Automatically evaluates strategies when needed
   - Independent of the web UI

3. **Web UI** (`pages/live_trading_v2.py`)
   - Control panel for starting/stopping trading
   - Configuration management
   - View strategy results and trade history
   - Monitor trading status

### Database Schema

The system uses SQLite with the following tables:

- `strategy_evaluations` - Results from backtesting all strategies
- `best_strategies` - Best strategy for each ticker
- `trading_config` - Trading parameters (tickers, risk, etc.)
- `trading_state` - Current state (active/inactive, timestamps)
- `trade_history` - All executed trades

## Quick Start

### Step 1: Start the Daemon

```bash
# Make scripts executable (first time only)
chmod +x start_daemon.sh stop_daemon.sh

# Start the daemon
./start_daemon.sh
```

The daemon will start in the background and wait for you to activate trading.

### Step 2: Configure Trading

1. Open the web interface: `streamlit run app.py`
2. Navigate to **Live Trading V2**
3. Configure your settings in the sidebar:
   - Trading mode (Paper/Live)
   - Stock symbols
   - Initial capital
   - Risk per trade
   - Max positions
   - Check interval
4. Click **Save Configuration**

### Step 3: Start Trading

1. Click **START TRADING** in the Control Panel
2. The daemon will:
   - Load your configuration
   - Evaluate ALL 11 strategies for each ticker (if not already done)
   - Select the best strategy for each ticker
   - Begin checking for signals at your specified interval
   - Execute trades automatically

### Step 4: Monitor

- View real-time status in the Control Panel
- Check Strategy Results to see which strategy was chosen for each ticker
- Monitor your Portfolio
- Review Trade History

### Step 5: Stop Trading

Click **STOP TRADING** when you want to stop. The daemon will:
- Complete the current cycle
- Stop checking for new signals
- Remain running but inactive

### Step 6: Stop the Daemon

When you want to completely shut down the daemon:

```bash
./stop_daemon.sh
```

## Key Features

### Automatic Strategy Evaluation

When you start trading, the system automatically:

1. Checks if strategies have been evaluated for your tickers
2. If not, runs backtests for ALL 11 strategies
3. Saves results to the database
4. Selects the best strategy based on your chosen metric (default: Sharpe Ratio)
5. Uses the best strategy for live trading

**Available Strategies:**
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
- Adaptive ML

### Persistent State

Everything is saved to `data/trading_state.db`:

- **Strategy evaluations** - Saved permanently, no need to re-evaluate
- **Trading configuration** - Restored on restart
- **Trading state** - Daemon knows if trading should be active
- **Trade history** - All trades are recorded

This means:
- Close your laptop → Trading continues
- Restart the daemon → It picks up where it left off
- Crash recovery → State is preserved

### Background Daemon

The daemon runs independently:

- Separate process from the web UI
- Can close the web browser completely
- Checks trading state periodically
- Executes trades based on best strategies
- Logs everything to `data/trading_daemon.log`

## Configuration Options

### Trading Mode
- **Paper Trading** (recommended): Test with paper money
- **Live Trading**: Real money (use with caution!)

### Risk Management
- **Initial Capital**: Starting capital amount
- **Risk Per Trade**: Max % of capital per trade (1-10%)
- **Max Positions**: Maximum concurrent positions (1-10)

### Timing
- **Check Interval**: How often to check for signals (60-3600 seconds)
  - 300 seconds (5 minutes) is recommended
  - Lower values = more frequent checks, higher API usage
  - Higher values = less frequent checks, may miss opportunities

## Monitoring & Logs

### Daemon Logs

```bash
# View real-time logs
tail -f data/trading_daemon.log

# View output logs
tail -f data/daemon_output.log
```

### Database

```bash
# View database
sqlite3 data/trading_state.db

# Example queries
SELECT * FROM best_strategies;
SELECT * FROM trade_history ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM trading_state;
```

## Troubleshooting

### Daemon Won't Start

```bash
# Check if already running
pgrep -f trading_daemon

# Force kill if needed
pkill -f trading_daemon

# Start again
./start_daemon.sh
```

### Trading Not Executing

1. Check daemon is running: `pgrep -f trading_daemon`
2. Check trading is active in the UI
3. Check daemon logs: `tail -f data/trading_daemon.log`
4. Verify Alpaca credentials are set in `.streamlit/secrets.toml`

### Strategy Evaluation Errors

- Ensure you have enough historical data (strategies need 365 days)
- Check that tickers are valid
- Review logs for specific errors

### Database Issues

```bash
# Backup database
cp data/trading_state.db data/trading_state_backup.db

# Clear evaluations to force re-evaluation
sqlite3 data/trading_state.db "DELETE FROM strategy_evaluations; DELETE FROM best_strategies;"
```

## Best Practices

### Testing

1. **Always start with paper trading**
2. Test with a small number of tickers first (1-3)
3. Monitor for at least a week before considering live trading
4. Review trade history regularly

### Risk Management

1. Start with low risk per trade (1-2%)
2. Limit number of positions (3-5)
3. Don't risk more than you can afford to lose
4. Monitor your portfolio daily

### Strategy Selection

- The system uses Sharpe Ratio by default to select strategies
- Sharpe Ratio balances returns and risk
- Review the Strategy Results tab to see all strategy performance
- You can manually re-evaluate strategies by clearing the database

### Monitoring

1. Check daemon logs daily: `tail -f data/trading_daemon.log`
2. Review trade history in the UI
3. Monitor your Alpaca account separately
4. Set up alerts for your Alpaca account

## Comparison: V1 vs V2

| Feature | V1 | V2 |
|---------|----|----|
| Persistence | ❌ Restarts on every login | ✅ Continuous operation |
| Strategy Selection | Manual | ✅ Automatic (all strategies) |
| Runs when laptop closed | ❌ No | ✅ Yes |
| Background process | ❌ No | ✅ Yes |
| State preservation | ❌ No | ✅ Database-backed |
| Re-evaluation needed | ✅ Every time | ❌ Cached in DB |

## Migration from V1 to V2

If you were using Live Trading V1:

1. **Stop any running V1 trading sessions**
2. **Start the V2 daemon**: `./start_daemon.sh`
3. **Configure in the V2 UI** with your desired settings
4. **Start trading** - the system will evaluate strategies fresh

Your old V1 sessions won't interfere with V2.

## Advanced Usage

### Custom Check Intervals

For different trading styles:

- **Day Trading**: 60-300 seconds (1-5 minutes)
- **Swing Trading**: 300-900 seconds (5-15 minutes)
- **Position Trading**: 1800-3600 seconds (30-60 minutes)

### Multiple Tickers

The system handles multiple tickers efficiently:
- Each ticker gets its own best strategy
- Strategies are evaluated in parallel during backtesting
- Position limits prevent over-exposure

### Re-evaluation

To force re-evaluation of strategies:

```bash
sqlite3 data/trading_state.db
DELETE FROM strategy_evaluations WHERE ticker = 'AAPL';
DELETE FROM best_strategies WHERE ticker = 'AAPL';
.exit
```

The daemon will re-evaluate on next cycle.

## Support

For issues or questions:

1. Check the logs: `tail -f data/trading_daemon.log`
2. Review this guide
3. Check Alpaca API status: https://status.alpaca.markets/
4. Review your Alpaca account for actual trade execution

## Security Notes

- API keys are stored in `.streamlit/secrets.toml`
- Database is local to your machine
- Daemon runs with your user permissions
- Always use paper trading first
- Never share your Alpaca API keys

## System Requirements

- Python 3.8+
- All requirements from `requirements.txt`
- Active Alpaca account
- Sufficient disk space for logs and database
- Internet connection for market data and trading

## Future Enhancements

Planned improvements:

- Email/SMS alerts for trades
- Performance analytics dashboard
- Strategy parameter optimization
- Multi-timeframe analysis
- Custom strategy upload
- Risk management rules engine

---

**Remember**: This system trades with real money when in Live Trading mode. Always test thoroughly with paper trading first!
