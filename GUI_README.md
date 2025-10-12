# 🎨 GUI Application - Quick Guide

## 🚀 Launch the GUI

```bash
# Option 1: Use the launcher script
./run_gui.sh

# Option 2: Direct command
streamlit run app.py
```

The application will open automatically in your browser at `http://localhost:8501`

## ✨ What You Get

A beautiful web interface with:

- 📊 **Interactive Dashboard** - No coding required!
- 🎯 **Strategy Selection** - SMA Crossover, RSI, MACD
- 📈 **Real-time Charts** - Plotly interactive visualizations
- 💼 **Performance Metrics** - Sharpe Ratio, Win Rate, Drawdown, etc.
- 📋 **Trade History** - Complete trade log with CSV export
- ⚙️ **Parameter Tuning** - Adjust strategy parameters with sliders
- 🎨 **Modern UI** - Clean, professional interface

## 🎯 Quick Start (30 seconds)

1. Launch: `./run_gui.sh`
2. Keep default settings (AAPL, SMA Crossover)
3. Click "🚀 Run Backtest"
4. View beautiful results!

## 📱 Interface Overview

### Sidebar
- Strategy selection
- Stock symbol input
- Date range picker
- Parameter sliders
- Advanced settings

### Main Panel
- Welcome screen (before backtest)
- Performance metrics (5 key metrics)
- Interactive charts (portfolio value & drawdown)
- Trade statistics
- Complete trade history
- CSV export button

## 💡 Example Workflows

### Test AAPL with SMA
```
1. Strategy: SMA Crossover
2. Symbol: AAPL
3. Dates: 2023-01-01 to 2024-10-01
4. Click Run Backtest
```

### Optimize RSI for TSLA
```
1. Strategy: RSI
2. Symbol: TSLA
3. Adjust RSI Period slider
4. Run multiple times with different values
5. Compare Sharpe Ratios
```

### Compare MACD Parameters
```
1. Strategy: MACD
2. Symbol: MSFT
3. Try Fast: 8, Slow: 21, Signal: 9
4. Then try Fast: 12, Slow: 26, Signal: 9
5. Compare total returns
```

## 📊 Key Metrics Explained

| Metric | Good Value | What It Means |
|--------|-----------|---------------|
| Total Return | >10%/year | Overall profit/loss |
| Sharpe Ratio | >1.0 | Risk-adjusted return |
| Max Drawdown | <20% | Largest loss from peak |
| Win Rate | >50% | % of winning trades |
| Profit Factor | >1.5 | Profits/Losses ratio |

## 🎨 Features

✅ **No coding required** - Point and click interface  
✅ **Interactive charts** - Zoom, pan, hover for details  
✅ **Real-time feedback** - Loading spinners and status  
✅ **Export data** - Download trade history as CSV  
✅ **Parameter optimization** - Test different settings easily  
✅ **Professional metrics** - Industry-standard calculations  
✅ **Beautiful design** - Modern, clean interface  

## 🔧 Tips

- **Use 1+ year of data** for reliable results
- **Test multiple date ranges** to validate strategy
- **Adjust one parameter at a time** to see effects
- **Export trade history** for further analysis
- **Start with defaults** before optimizing

## 📚 Documentation

- **GUI_GUIDE.md** - Complete interface guide
- **STRATEGIES_GUIDE.md** - Strategy explanations
- **QUICKSTART.md** - CLI usage guide

## 🎉 Enjoy!

The GUI makes algorithmic trading accessible to everyone. No programming knowledge needed - just point, click, and analyze!

---

**Note:** This is a backtesting tool. Always paper trade before risking real money!
