# Live Trading V2.5 - Streamlit Cloud Compatible Version

## Overview

**Live Trading V2.5** is specifically designed to work on **Streamlit Cloud** while addressing your requirements for automatic strategy evaluation and best strategy selection.

### What V2.5 Offers

✅ **Automatic Strategy Evaluation** - All 11 strategies tested automatically
✅ **Best Strategy Selection** - System picks highest Sharpe Ratio strategy
✅ **Session Persistence** - Data preserved during your browser session
✅ **Auto-Refresh** - Continuous operation while browser is open
✅ **Cloud Compatible** - Works perfectly on Streamlit Cloud (free hosting)

### Limitations

⚠️ **Browser must stay open** - Trading stops when you close the browser tab
⚠️ **Session-based** - Evaluation results and trade history lost when browser closes
⚠️ **Not 24/7** - Cannot run when computer is off (unlike V2 with daemon)

## Quick Start on Streamlit Cloud

### 1. Deploy to Streamlit Cloud

Your app is already configured for Streamlit Cloud. Just:

1. Push code to GitHub
2. Deploy from Streamlit Cloud dashboard
3. Add Alpaca secrets in Streamlit Cloud settings

### 2. Use the App

1. **Open the app** on Streamlit Cloud
2. **Navigate to Live Trading V2.5** (Cloud button)
3. **Configure** your settings in the sidebar:
   - Trading mode (Paper/Live)
   - Stock symbols (one per line)
   - Risk parameters
   - Check interval (120 seconds recommended)
4. **Click "Save Configuration"**
5. **Click "Evaluate All Strategies"**
   - This tests all 11 strategies on your tickers
   - Takes ~5-10 minutes
   - Only needed once per session
6. **Click "START TRADING"**
7. **Keep the browser tab open** - Trading will continue automatically

## How It Works

### Strategy Evaluation

When you click "Evaluate All Strategies":

```
For AAPL:
  Testing SMA Crossover...     Sharpe: 0.85
  Testing RSI...               Sharpe: 1.23
  Testing MACD...              Sharpe: 0.92
  Testing Bollinger Bands...   Sharpe: 1.15
  Testing Momentum...          Sharpe: 1.45 ← BEST!
  Testing Mean Reversion...    Sharpe: 0.78
  Testing Breakout...          Sharpe: 0.95
  Testing VWAP...              Sharpe: 1.02
  Testing Pairs Trading...     Sharpe: 0.88
  Testing ML Strategy...       Sharpe: 1.12
  Testing Adaptive ML...       Sharpe: 1.33

✅ Selected: Momentum (Sharpe: 1.45)
```

This happens automatically for each ticker you provide!

### Automatic Trading Loop

Once started:

1. **Every N seconds** (you configure this):
   - Get current market data
   - Generate signals using best strategies
   - Execute BUY/SELL orders if needed
   - Update display
   - Auto-refresh page

2. **While trading**:
   - Keep browser tab open
   - Monitor in real-time
   - View signals and trades
   - Check portfolio

3. **Stop anytime**:
   - Click "STOP TRADING" button
   - Trading halts immediately

## Configuration Options

### Trading Parameters

- **Mode**: Paper (recommended) or Live Trading
- **Tickers**: Any valid stock symbols
- **Initial Capital**: Starting balance
- **Risk per Trade**: 1-10% of capital
- **Max Positions**: 1-10 concurrent positions
- **Check Interval**: 60-600 seconds between signal checks

### Recommended Settings for Cloud

```yaml
Trading Mode: Paper Trading
Tickers: 2-3 stocks (start small)
Risk per Trade: 2%
Max Positions: 3
Check Interval: 120 seconds (2 minutes)
```

Lower intervals = more API calls = may hit rate limits

## Features

### 1. Automatic Strategy Evaluation

- Tests all 11 strategies automatically
- No manual selection needed
- Results shown in Strategy Results tab
- See performance comparison for all strategies

### 2. Best Strategy Selection

- Uses Sharpe Ratio to select best strategy
- Balances returns and risk
- Different strategy may be best for each ticker
- View full rankings in Strategy Results tab

### 3. Session Persistence

- Configuration saved during session
- Evaluation results preserved
- Trade history accumulated
- Portfolio state maintained
- **Lost when browser closes**

### 4. Auto-Refresh Trading

- Page refreshes automatically every 2 seconds
- Checks for signals at your interval
- Executes trades automatically
- Display updates in real-time

## Comparison: V1 vs V2.5 vs V2

| Feature | V1 | V2.5 (Cloud) | V2 (VPS) |
|---------|----|--------------| ---------|
| **Deployment** | Cloud | Cloud | Local/VPS |
| **Strategy Selection** | Manual | ✅ Auto (all 11) | ✅ Auto (all 11) |
| **Best Strategy** | Manual | ✅ Automatic | ✅ Automatic |
| **Persistence** | Session | Session | ✅ Database |
| **Runs when closed** | ❌ No | ❌ No | ✅ Yes (24/7) |
| **Browser required** | ✅ Yes | ✅ Yes | ❌ No (daemon) |
| **Free hosting** | ✅ Yes | ✅ Yes | ❌ No ($5-10/mo) |
| **Setup complexity** | Easy | Easy | Medium |

## Best Practices

### For Streamlit Cloud Deployment

1. **Start with Paper Trading**
   - Test thoroughly before live money
   - Monitor for at least a week

2. **Keep Browser Open**
   - Use dedicated browser window
   - Prevent computer sleep
   - Consider using a tablet/old device

3. **Start Small**
   - 2-3 tickers initially
   - Low risk per trade (1-2%)
   - Few positions (3-5)

4. **Monitor Regularly**
   - Check every few hours
   - Review trade history
   - Monitor Alpaca account directly

5. **Manage Check Intervals**
   - 120-300 seconds recommended
   - Lower = more API calls
   - Higher = may miss opportunities

### Trading Hours

Since browser must stay open:

- **Day Trading**: Keep browser open during market hours (9:30 AM - 4:00 PM ET)
- **Swing Trading**: Can close overnight, restart in morning
- **Extended Hours**: Requires browser open extended hours

## Limitations & Workarounds

### Limitation 1: Browser Must Stay Open

**Workaround Options:**
- Use a dedicated device (old laptop, tablet)
- Keep computer awake (disable sleep)
- Use a remote desktop (VNC, TeamViewer)
- Upgrade to V2 on a VPS for 24/7 operation

### Limitation 2: Session-Based Persistence

**Impact:**
- Evaluation results lost when browser closes
- Need to re-evaluate after closing browser
- Trade history lost (but trades are in Alpaca)

**Workaround:**
- Evaluation takes ~5-10 min once per session
- Trade history still in Alpaca account
- For permanent storage, use V2

### Limitation 3: Streamlit Cloud Restarts

**Streamlit Cloud may restart your app:**
- After periods of inactivity (~10-15 minutes)
- During deployments
- If memory limits exceeded

**Impact:**
- Trading stops during restart
- Need to restart manually
- Active positions remain in Alpaca

**Workaround:**
- Monitor regularly
- Set up Alpaca alerts
- For critical trading, use V2 on VPS

## Troubleshooting

### Trading Stops Unexpectedly

**Causes:**
- Browser tab closed
- Computer went to sleep
- Internet connection lost
- Streamlit Cloud restart

**Solutions:**
- Check browser tab is open
- Disable computer sleep
- Check internet connection
- Restart trading if needed

### Evaluation Takes Too Long

**Causes:**
- Many tickers
- Slow API responses
- Complex strategies (ML)

**Solutions:**
- Reduce number of tickers
- Test with 1-2 tickers first
- Be patient (5-10 min normal)

### Trades Not Executing

**Checks:**
1. Trading is active (green status)
2. Alpaca credentials configured
3. Market is open
4. Signals are not all HOLD
5. Not at max positions

**Solutions:**
- Check logs for errors
- Verify Alpaca account status
- Check market hours
- Review signal diagnostics

## Monitoring

### In the UI

1. **Control Panel Tab**
   - Trading status (green/red)
   - Last check time
   - Configuration

2. **Strategy Results Tab**
   - Best strategies per ticker
   - All strategy comparisons
   - Performance metrics

3. **Portfolio Tab**
   - Current positions
   - Account value
   - Buying power

4. **Trade History Tab**
   - All trades this session
   - Buy/sell counts
   - Timestamps

### In Alpaca

- Check your Alpaca dashboard regularly
- Set up Alpaca email alerts
- Review actual trade executions
- Verify positions match

## When to Use V2.5 vs V2

### Use V2.5 (Cloud) When:

✅ You want free hosting on Streamlit Cloud
✅ You can keep browser open during trading hours
✅ Day trading (market hours only)
✅ Testing and learning
✅ Don't want to manage a VPS

### Use V2 (VPS) When:

✅ You need 24/7 operation
✅ Want to close your laptop
✅ Need true persistence across restarts
✅ Serious/production trading
✅ Willing to pay $5-10/month for hosting

## Migration Path

### From V1 to V2.5

Simply switch to V2.5 page:
- No configuration changes needed
- All features work the same
- Plus automatic evaluation

### From V2.5 to V2

If you need 24/7 operation:

1. Deploy V2 to a VPS (see LIVE_TRADING_V2_GUIDE.md)
2. Start the daemon on VPS
3. Configure once
4. Trading continues 24/7

## Support

For issues:

1. **Check the Control Panel** for status
2. **Review Trade History** for activity
3. **Check Alpaca Account** for actual trades
4. **Verify Market Hours** (9:30 AM - 4:00 PM ET)
5. **Restart if needed** (stop & start trading)

## Summary

**V2.5 is perfect for Streamlit Cloud deployment with these benefits:**

✅ Automatic evaluation of all strategies
✅ Best strategy selection
✅ Free hosting
✅ Easy to use
✅ No server management

**Just remember:**
⚠️ Keep browser open while trading
⚠️ For 24/7 operation, use V2 on VPS

---

**Ready to start?** Deploy to Streamlit Cloud and navigate to Live Trading V2.5!
