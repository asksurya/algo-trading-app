# 🖥️ GUI Application Guide

## Overview

The Algorithmic Trading Platform features a beautiful web-based interface built with Streamlit. This GUI makes it easy to backtest trading strategies without writing any code!

## 🚀 Quick Start

### Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Launch the GUI:**
```bash
# Option 1: Use the launcher script
./run_gui.sh

# Option 2: Direct command
streamlit run app.py
```

The application will automatically open in your default web browser at `http://localhost:8501`

## 📱 Interface Overview

### Sidebar (Left Panel)

The sidebar contains all configuration options:

#### 1. **Strategy Selection**
- **SMA Crossover**: Simple moving average crossover strategy
- **RSI**: Relative Strength Index mean reversion strategy
- **MACD**: Moving Average Convergence Divergence strategy

#### 2. **Stock Symbol**
- Enter any valid stock ticker (e.g., AAPL, TSLA, MSFT, GOOGL)
- Symbol is automatically converted to uppercase

#### 3. **Date Range**
- **Start Date**: Beginning of backtest period
- **End Date**: End of backtest period
- ⚠️ Use historical dates only (past dates)
- Recommended: At least 1 year of data

#### 4. **Initial Capital**
- Set your starting portfolio value
- Default: $100,000
- Range: $1,000 - $10,000,000

#### 5. **Strategy Parameters**

**For SMA Crossover:**
- Short Window: 10-100 days (default: 50)
- Long Window: 100-300 days (default: 200)

**For RSI:**
- RSI Period: 5-30 days (default: 14)
- Oversold Threshold: 20-40 (default: 30)
- Overbought Threshold: 60-80 (default: 70)

**For MACD:**
- Fast Period: 8-20 days (default: 12)
- Slow Period: 20-35 days (default: 26)
- Signal Period: 5-15 days (default: 9)

#### 6. **Advanced Settings** (Expandable)
- Commission Rate: Trading commission per trade
- Slippage Rate: Expected price slippage

### Main Panel (Right Side)

#### Welcome Screen
When you first launch the app, you'll see:
- Getting started instructions
- Strategy descriptions
- Best practices tips

#### Results Screen (After Running Backtest)

**1. Performance Metrics (Top Row)**
- Total Return: Overall percentage gain/loss
- Sharpe Ratio: Risk-adjusted return metric
- Max Drawdown: Largest peak-to-trough decline
- Win Rate: Percentage of profitable trades
- Profit Factor: Gross profits / gross losses

**2. Performance Charts**
- **Portfolio Value Chart**: Shows equity curve over time with initial capital reference line
- **Drawdown Chart**: Visualizes portfolio drawdowns during the period

**3. Trade Statistics**
- **Summary Table**: Key trade metrics
- **Returns Distribution**: Histogram of profit/loss per trade

**4. Trade History**
- Complete list of all trades executed
- Entry/exit dates and prices
- Profit/loss for each trade
- Trade duration
- Download button for CSV export

## 💡 Usage Examples

### Example 1: Quick Backtest
1. Keep default settings (SMA Crossover, AAPL)
2. Select date range: Jan 1, 2023 - Oct 1, 2024
3. Click "🚀 Run Backtest"
4. View results in seconds!

### Example 2: Optimize RSI Strategy
1. Select "RSI" strategy
2. Enter symbol: "TSLA"
3. Set date range
4. Adjust RSI parameters:
   - Try Period: 10 (faster signals)
   - Oversold: 25
   - Overbought: 75
5. Run backtest and compare results

### Example 3: Compare Different Parameters
1. Run backtest with default parameters
2. Note the Sharpe Ratio and Total Return
3. Adjust parameters (e.g., change SMA windows to 20/50)
4. Run backtest again
5. Compare metrics to find optimal settings

## 📊 Understanding the Metrics

### Total Return
- **What it means**: Overall profit/loss percentage
- **Good benchmark**: > 10% annually
- **Formula**: (Final Value - Initial Capital) / Initial Capital × 100

### Sharpe Ratio
- **What it means**: Risk-adjusted return
- **Good benchmark**: 
  - \> 1.0 = Good
  - \> 2.0 = Excellent
  - \> 3.0 = Outstanding
- **Interpretation**: Higher is better; shows return per unit of risk

### Max Drawdown
- **What it means**: Largest peak-to-trough decline
- **Good benchmark**: < 20%
- **Interpretation**: Lower is better; shows maximum risk exposure

### Win Rate
- **What it means**: Percentage of profitable trades
- **Good benchmark**: > 50%
- **Note**: Can be misleading if average win < average loss

### Profit Factor
- **What it means**: Total profits / total losses
- **Good benchmark**: > 1.5
- **Interpretation**: > 1.0 means profitable overall

## 🎨 Features

### Interactive Charts
- **Hover**: See exact values at any point
- **Zoom**: Click and drag to zoom into specific periods
- **Pan**: Use mouse to navigate through time
- **Reset**: Double-click to reset zoom

### Data Export
- Download complete trade history as CSV
- Includes all trade details for further analysis
- File named: `{SYMBOL}_{STRATEGY}_trades.csv`

### Real-time Feedback
- Loading spinner during backtest execution
- Success/error messages
- Progress indicators

## 🔧 Tips & Best Practices

### For Backtesting
1. **Use Sufficient Data**: At least 1 year for reliable results
2. **Test Multiple Periods**: Try different date ranges
3. **Consider Market Conditions**: Bull vs bear markets behave differently
4. **Account for Costs**: Include realistic commission and slippage

### For Strategy Optimization
1. **Start with Defaults**: Test default parameters first
2. **Change One at a Time**: Isolate parameter effects
3. **Avoid Overfitting**: Don't over-optimize to historical data
4. **Paper Trade First**: Test in simulation before live trading

### Common Issues

**Issue**: "No results generated"
- **Solution**: Strategy may need more data. Try:
  - Longer date range (especially for SMA 200)
  - Different stock symbol
  - Adjusted parameters

**Issue**: Poor performance
- **Solution**: 
  - Not all strategies work for all stocks
  - Try different time periods
  - Consider market conditions

**Issue**: Slow loading
- **Solution**: 
  - First run downloads data (slower)
  - Subsequent runs use cache (faster)
  - Clear browser cache if needed

## 🎯 Workflow Example

1. **Research Phase**
   - Choose stock to analyze
   - Select appropriate strategy type
   - Decide on time period

2. **Initial Test**
   - Run backtest with default parameters
   - Review all metrics
   - Examine trade history

3. **Optimization**
   - Adjust one parameter at a time
   - Run multiple backtests
   - Compare results

4. **Validation**
   - Test on different time periods
   - Try different stocks
   - Verify consistency

5. **Documentation**
   - Export trade history
   - Screenshot key metrics
   - Note optimal parameters

## 🚫 Limitations

- **Historical Data Only**: Cannot predict future performance
- **No Live Trading**: This is a backtesting tool only
- **Perfect Information**: Assumes perfect execution (no missed fills)
- **Single Symbol**: One stock at a time
- **No Short Selling**: Long positions only

## 🔒 Privacy & Security

- **No Data Collection**: All data stays on your computer
- **Local Processing**: Backtests run locally
- **Market Data**: Downloaded from Yahoo Finance/Alpaca
- **No Login Required**: Free and open to use

## 💻 Technical Details

- **Framework**: Streamlit (Python)
- **Charting**: Plotly (interactive charts)
- **Data Source**: Yahoo Finance (via yfinance)
- **Backend**: Your existing backtesting engine
- **Browser**: Any modern browser (Chrome, Firefox, Safari, Edge)

## 📚 Further Reading

- [Streamlit Documentation](https://docs.streamlit.io)
- [STRATEGIES_GUIDE.md](STRATEGIES_GUIDE.md) - Strategy details
- [QUICKSTART.md](QUICKSTART.md) - CLI usage
- [README.md](README.md) - Full documentation

## 🆘 Support

If you encounter issues:
1. Check the terminal for error messages
2. Ensure all dependencies are installed
3. Verify internet connection (for data download)
4. Try clearing Streamlit cache: Hamburger menu → Clear cache

## 🎉 Have Fun!

Experiment with different strategies and parameters. Remember: **Past performance doesn't guarantee future results!**

Happy backtesting! 📈
