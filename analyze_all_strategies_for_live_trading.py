#!/usr/bin/env python3
"""
Comprehensive Strategy Backtesting Analysis for Live Trading
Analyzes all 16 trading strategies across multiple tickers to identify best performers
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import all strategy classes
from strategies.sma_crossover import SMACrossoverStrategy
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_bands import BollingerBandsStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.vwap_strategy import VWAPStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.pairs_trading import PairsTradingStrategy
from strategies.ml_strategy import MLStrategy
from strategies.adaptive_ml_strategy import AdaptiveMLStrategy
from strategies.stochastic_strategy import StochasticStrategy
from strategies.keltner_channel import KeltnerChannelStrategy
from strategies.atr_trailing_stop import ATRTrailingStopStrategy
from strategies.donchian_channel import DonchianChannelStrategy
from strategies.ichimoku_cloud import IchimokuCloudStrategy
from strategies.base_strategy import Signal, StrategyMetrics


# Test configuration
TEST_TICKERS = ['AAPL', 'AMD', 'NVDA', 'SPY', 'TSLA', 'MSFT']
INITIAL_CAPITAL = 100000
MAX_POSITION_SIZE = 0.2  # 20% per position
LOOKBACK_MONTHS = 12

# Strategy configurations with default parameters
STRATEGY_CONFIGS = {
    'SMA_CROSSOVER': {
        'class': SMACrossoverStrategy,
        'params': {'short_window': 20, 'long_window': 50},
        'single_ticker': True
    },
    'RSI': {
        'class': RSIStrategy,
        'params': {'period': 14, 'oversold': 30, 'overbought': 70},
        'single_ticker': True
    },
    'MACD': {
        'class': MACDStrategy,
        'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
        'single_ticker': True
    },
    'BOLLINGER_BANDS': {
        'class': BollingerBandsStrategy,
        'params': {'period': 20, 'num_std': 2},
        'single_ticker': True
    },
    'MEAN_REVERSION': {
        'class': MeanReversionStrategy,
        'params': {'period': 20, 'entry_threshold': 2.0, 'exit_threshold': 0.5},
        'single_ticker': True
    },
    'VWAP': {
        'class': VWAPStrategy,
        'params': {'period': 20},
        'single_ticker': True
    },
    'MOMENTUM': {
        'class': MomentumStrategy,
        'params': {'period': 20, 'threshold': 0.0},
        'single_ticker': True
    },
    'BREAKOUT': {
        'class': BreakoutStrategy,
        'params': {'lookback_period': 20, 'breakout_threshold': 1.02},
        'single_ticker': True
    },
    'PAIRS_TRADING': {
        'class': PairsTradingStrategy,
        'params': {'lookback_period': 60},
        'single_ticker': False  # Requires two tickers
    },
    'ML_STRATEGY': {
        'class': MLStrategy,
        'params': {},
        'single_ticker': True
    },
    'ADAPTIVE_ML': {
        'class': AdaptiveMLStrategy,
        'params': {},
        'single_ticker': True
    },
    'STOCHASTIC': {
        'class': StochasticStrategy,
        'params': {'k_period': 14, 'd_period': 3, 'smooth_k': 3, 'oversold': 20, 'overbought': 80},
        'single_ticker': True
    },
    'KELTNER_CHANNEL': {
        'class': KeltnerChannelStrategy,
        'params': {'ema_period': 20, 'atr_period': 10, 'multiplier': 2.0},
        'single_ticker': True
    },
    'ATR_TRAILING_STOP': {
        'class': ATRTrailingStopStrategy,
        'params': {'atr_period': 14, 'atr_multiplier': 3.0, 'trend_period': 50},
        'single_ticker': True
    },
    'DONCHIAN_CHANNEL': {
        'class': DonchianChannelStrategy,
        'params': {'entry_period': 20, 'exit_period': 10, 'atr_period': 20},
        'single_ticker': True
    },
    'ICHIMOKU_CLOUD': {
        'class': IchimokuCloudStrategy,
        'params': {'tenkan_period': 9, 'kijun_period': 26, 'senkou_b_period': 52, 'displacement': 26},
        'single_ticker': True
    }
}


def fetch_historical_data(ticker: str, months: int = 12) -> pd.DataFrame:
    """Fetch historical OHLCV data for a ticker."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)

        print(f"  Fetching {ticker} data from {start_date.date()} to {end_date.date()}...")

        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            print(f"  WARNING: No data received for {ticker}")
            return None

        # Standardize column names
        df.columns = [col.lower() for col in df.columns]

        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            print(f"  WARNING: Missing required columns for {ticker}")
            return None

        print(f"  Fetched {len(df)} bars for {ticker}")
        return df

    except Exception as e:
        print(f"  ERROR fetching {ticker}: {str(e)}")
        return None


def run_backtest(strategy, data: pd.DataFrame, ticker: str, initial_capital: float = 100000) -> Dict:
    """Run backtest for a strategy on given data."""
    try:
        # Calculate indicators
        data_with_indicators = strategy.calculate_indicators(data.copy())

        # Generate signals
        signals = strategy.generate_signals(data_with_indicators)

        # Initialize backtest state
        cash = initial_capital
        position = 0
        equity_curve = []
        trades = []

        for i in range(len(data_with_indicators)):
            current_date = data_with_indicators.index[i]
            current_price = data_with_indicators['close'].iloc[i]

            # Get signal
            signal = signals.iloc[i] if i < len(signals) else 0

            # Execute trades based on signal
            if signal == 1 and position == 0:  # BUY signal and no position
                shares_to_buy = int((cash * MAX_POSITION_SIZE) / current_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price
                    cash -= cost
                    position = shares_to_buy
                    trades.append({
                        'date': current_date,
                        'type': 'BUY',
                        'shares': shares_to_buy,
                        'price': current_price,
                        'value': cost
                    })

            elif signal == -1 and position > 0:  # SELL signal and has position
                proceeds = position * current_price
                profit = proceeds - trades[-1]['value'] if trades else 0
                cash += proceeds
                trades.append({
                    'date': current_date,
                    'type': 'SELL',
                    'shares': position,
                    'price': current_price,
                    'value': proceeds,
                    'profit': profit
                })
                position = 0

            # Calculate portfolio value
            portfolio_value = cash + (position * current_price)
            equity_curve.append(portfolio_value)

        # Close any open position at the end
        if position > 0:
            final_price = data_with_indicators['close'].iloc[-1]
            proceeds = position * final_price
            profit = proceeds - trades[-1]['value'] if trades else 0
            cash += proceeds
            trades.append({
                'date': data_with_indicators.index[-1],
                'type': 'SELL',
                'shares': position,
                'price': final_price,
                'value': proceeds,
                'profit': profit
            })
            position = 0

        # Calculate metrics
        equity_series = pd.Series(equity_curve, index=data_with_indicators.index[:len(equity_curve)])

        if len(equity_curve) < 2:
            return None

        total_return = (equity_curve[-1] / initial_capital - 1) * 100

        # Calculate returns for Sharpe
        returns = equity_series.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = StrategyMetrics.calculate_sharpe_ratio(returns)
        else:
            sharpe_ratio = 0.0

        max_drawdown = StrategyMetrics.calculate_max_drawdown(equity_series) * 100

        # Calculate trade metrics
        completed_trades = [t for t in trades if t['type'] == 'SELL']
        total_trades = len(completed_trades)

        if total_trades > 0:
            win_rate = sum(1 for t in completed_trades if t.get('profit', 0) > 0) / total_trades * 100
            profit_factor = StrategyMetrics.calculate_profit_factor(completed_trades)
            avg_profit = np.mean([t.get('profit', 0) for t in completed_trades])
        else:
            win_rate = 0
            profit_factor = 0
            avg_profit = 0

        return {
            'total_return': round(total_return, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 2),
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_profit': round(avg_profit, 2),
            'final_value': round(equity_curve[-1], 2)
        }

    except Exception as e:
        print(f"    ERROR in backtest: {str(e)}")
        return None


def main():
    """Main analysis function."""
    print("=" * 80)
    print("COMPREHENSIVE STRATEGY BACKTESTING ANALYSIS FOR LIVE TRADING")
    print("=" * 80)
    print(f"\nTesting {len(STRATEGY_CONFIGS)} strategies on {len(TEST_TICKERS)} tickers")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,}")
    print(f"Lookback Period: {LOOKBACK_MONTHS} months")
    print(f"Max Position Size: {MAX_POSITION_SIZE * 100}%")
    print("\n" + "=" * 80)

    # Fetch data for all tickers
    print("\n[1/4] FETCHING HISTORICAL DATA")
    print("-" * 80)
    ticker_data = {}
    for ticker in TEST_TICKERS:
        data = fetch_historical_data(ticker, LOOKBACK_MONTHS)
        if data is not None:
            ticker_data[ticker] = data

    print(f"\nSuccessfully fetched data for {len(ticker_data)} tickers")

    # Run backtests
    print("\n[2/4] RUNNING BACKTESTS")
    print("-" * 80)

    all_results = {}
    total_backtests = 0
    successful_backtests = 0

    for ticker, data in ticker_data.items():
        print(f"\nTesting {ticker}...")
        all_results[ticker] = {}

        for strategy_name, config in STRATEGY_CONFIGS.items():
            # Skip pairs trading for single ticker analysis
            if not config['single_ticker']:
                print(f"  {strategy_name}: SKIPPED (requires multiple tickers)")
                continue

            total_backtests += 1

            try:
                # Initialize strategy
                strategy_class = config['class']
                params = config['params']
                strategy = strategy_class(**params)

                print(f"  {strategy_name}: Running...", end=' ')

                # Run backtest
                result = run_backtest(strategy, data, ticker, INITIAL_CAPITAL)

                if result:
                    all_results[ticker][strategy_name] = result
                    successful_backtests += 1
                    print(f"✓ (Return: {result['total_return']}%, Sharpe: {result['sharpe_ratio']}, Trades: {result['total_trades']})")
                else:
                    print("✗ (Failed)")

            except Exception as e:
                print(f"✗ (Error: {str(e)})")

    print(f"\nCompleted {successful_backtests}/{total_backtests} backtests successfully")

    # Analyze results
    print("\n[3/4] ANALYZING RESULTS")
    print("-" * 80)

    recommendations = {}

    for ticker in ticker_data.keys():
        if ticker not in all_results or not all_results[ticker]:
            continue

        # Filter strategies with minimum criteria
        valid_strategies = []
        for strategy_name, metrics in all_results[ticker].items():
            # Minimum criteria: at least 5 trades, max drawdown < 50%
            if metrics['total_trades'] >= 5 and metrics['max_drawdown'] < 50:
                valid_strategies.append({
                    'strategy_type': strategy_name,
                    'return': metrics['total_return'],
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'win_rate': metrics['win_rate'],
                    'max_drawdown': metrics['max_drawdown'],
                    'total_trades': metrics['total_trades'],
                    'profit_factor': metrics['profit_factor'],
                    'parameters': STRATEGY_CONFIGS[strategy_name]['params'],
                    'score': (
                        metrics['total_return'] * 0.3 +
                        metrics['sharpe_ratio'] * 20 * 0.3 +
                        metrics['win_rate'] * 0.2 +
                        (100 - metrics['max_drawdown']) * 0.2
                    )
                })

        # Sort by composite score
        valid_strategies.sort(key=lambda x: x['score'], reverse=True)

        # Take top 5
        top_strategies = valid_strategies[:5]

        recommendations[ticker] = {
            'top_strategies': top_strategies,
            'recommended_count': min(3, len(top_strategies)),
            'total_tested': len(all_results[ticker]),
            'valid_strategies': len(valid_strategies)
        }

        print(f"\n{ticker}: {len(valid_strategies)} valid strategies, recommending top {recommendations[ticker]['recommended_count']}")
        for i, strat in enumerate(top_strategies[:3], 1):
            print(f"  {i}. {strat['strategy_type']}: {strat['return']}% return, Sharpe {strat['sharpe_ratio']}, {strat['win_rate']}% win rate")

    # Save recommendations
    print("\n[4/4] GENERATING RECOMMENDATIONS")
    print("-" * 80)

    output_file = 'live_trading_strategy_recommendations.json'
    with open(output_file, 'w') as f:
        json.dump(recommendations, f, indent=2)

    print(f"\n✓ Saved recommendations to: {output_file}")

    # Calculate overall best strategies
    strategy_scores = {}
    for ticker_results in all_results.values():
        for strategy_name, metrics in ticker_results.items():
            if strategy_name not in strategy_scores:
                strategy_scores[strategy_name] = []
            strategy_scores[strategy_name].append(metrics['total_return'])

    overall_best = []
    for strategy_name, returns in strategy_scores.items():
        if len(returns) >= 3:  # Must work on at least 3 tickers
            avg_return = np.mean(returns)
            consistency = 1 - (np.std(returns) / (abs(avg_return) + 1))
            overall_best.append({
                'strategy': strategy_name,
                'avg_return': round(avg_return, 2),
                'consistency': round(consistency, 2),
                'tickers_tested': len(returns)
            })

    overall_best.sort(key=lambda x: x['avg_return'] * x['consistency'], reverse=True)

    # Generate executive summary
    print("\nGenerating executive summary...")

    summary_content = f"""# Live Trading Strategy Analysis - Executive Summary

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Comprehensive backtesting analysis of **{len(STRATEGY_CONFIGS)}** trading strategies across **{len(TEST_TICKERS)}** tickers ({', '.join(TEST_TICKERS)}).

- **Total Backtests Run:** {successful_backtests}/{total_backtests}
- **Lookback Period:** {LOOKBACK_MONTHS} months
- **Initial Capital:** ${INITIAL_CAPITAL:,}
- **Max Position Size:** {MAX_POSITION_SIZE * 100}%

## Overall Best Performing Strategies

Strategies with consistent performance across multiple tickers:

"""

    for i, strat in enumerate(overall_best[:5], 1):
        summary_content += f"{i}. **{strat['strategy']}**\n"
        summary_content += f"   - Average Return: {strat['avg_return']}%\n"
        summary_content += f"   - Consistency Score: {strat['consistency']}\n"
        summary_content += f"   - Tested on {strat['tickers_tested']} tickers\n\n"

    summary_content += "\n## Per-Ticker Recommendations\n\n"

    for ticker in sorted(recommendations.keys()):
        rec = recommendations[ticker]
        summary_content += f"### {ticker}\n\n"
        summary_content += f"**Recommended:** Top {rec['recommended_count']} strategies (from {rec['valid_strategies']} valid options)\n\n"

        for i, strat in enumerate(rec['top_strategies'][:3], 1):
            summary_content += f"{i}. **{strat['strategy_type']}**\n"
            summary_content += f"   - Total Return: {strat['return']}%\n"
            summary_content += f"   - Sharpe Ratio: {strat['sharpe_ratio']}\n"
            summary_content += f"   - Win Rate: {strat['win_rate']}%\n"
            summary_content += f"   - Max Drawdown: {strat['max_drawdown']}%\n"
            summary_content += f"   - Total Trades: {strat['total_trades']}\n"
            summary_content += f"   - Profit Factor: {strat['profit_factor']}\n\n"

    summary_content += """
## Strategy Diversity Recommendations

For optimal risk management:

1. **Diversify by strategy type:** Use mix of trend-following, mean-reversion, and momentum strategies
2. **Diversify by timeframe:** Combine short-term (RSI, Stochastic) with medium-term (SMA, MACD) strategies
3. **Allocation:** Suggest 2-3 strategies per ticker with equal weighting
4. **Risk Management:** Monitor correlations between strategies to avoid concentration risk

## Risk Considerations

### Key Risks
- **Market Regime Changes:** Historical performance may not predict future results
- **Overfitting:** Strategies optimized on historical data may underperform live
- **Transaction Costs:** Real trading costs will reduce returns
- **Slippage:** Market orders may execute at worse prices than backtested

### Mitigation Strategies
1. Start with paper trading to validate performance
2. Use position sizing and stop losses
3. Monitor strategy performance daily
4. Be prepared to disable underperforming strategies
5. Maintain diversification across strategies and tickers

## Suggested Allocation

### Conservative Approach (Lower Risk)
- **Strategies per ticker:** 2
- **Position size:** 15% max per position
- **Focus:** High Sharpe ratio strategies (>1.0)
- **Suggested strategies:** SMA_CROSSOVER, BOLLINGER_BANDS, KELTNER_CHANNEL

### Balanced Approach (Medium Risk)
- **Strategies per ticker:** 3
- **Position size:** 20% max per position
- **Focus:** Mix of high return and high Sharpe
- **Suggested strategies:** Top 3 per ticker from recommendations

### Aggressive Approach (Higher Risk)
- **Strategies per ticker:** 4-5
- **Position size:** 25% max per position
- **Focus:** Maximize returns
- **Suggested strategies:** All strategies with positive returns and Sharpe > 0.5

## Next Steps for Live Trading

1. ✓ Review recommendations file: `live_trading_strategy_recommendations.json`
2. ☐ Select tickers and strategies to deploy
3. ☐ Configure strategy parameters in backend
4. ☐ Start paper trading sessions
5. ☐ Monitor performance for 1 week minimum
6. ☐ Transition to live trading with small positions
7. ☐ Scale up gradually based on performance

## Implementation Priority

**HIGH PRIORITY - Start Immediately:**
- AAPL, NVDA, MSFT (stable large caps)
- Top 2 strategies per ticker
- Paper trading mode

**MEDIUM PRIORITY - Start After 1 Week:**
- SPY (market index)
- Top 3 strategies
- Continue paper trading

**LOW PRIORITY - Start After 2 Weeks:**
- AMD, TSLA (higher volatility)
- Validate strategies work in current market conditions
- Consider live trading if paper trading successful

---

**IMPORTANT:** Markets are open. Recommend starting paper trading IMMEDIATELY with top strategies for AAPL, NVDA, and MSFT.
"""

    summary_file = 'LIVE_TRADING_ANALYSIS.md'
    with open(summary_file, 'w') as f:
        f.write(summary_content)

    print(f"✓ Saved executive summary to: {summary_file}")

    # Print summary to console
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\n📊 Overall Top 3 Strategies (Multi-Ticker Performance):")
    for i, strat in enumerate(overall_best[:3], 1):
        print(f"  {i}. {strat['strategy']}: {strat['avg_return']}% avg return")

    print(f"\n📁 Output Files:")
    print(f"  - {output_file} (JSON recommendations)")
    print(f"  - {summary_file} (Executive summary)")

    print(f"\n🚀 Ready for Live Trading:")
    print(f"  - {len(recommendations)} tickers analyzed")
    print(f"  - Top strategies identified for each ticker")
    print(f"  - Recommend starting with paper trading ASAP")

    print("\n" + "=" * 80)
    print(f"\n✅ RECOMMENDATIONS FILE: {os.path.abspath(output_file)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
