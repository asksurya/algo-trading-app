#!/usr/bin/env python3
"""
Per-Ticker Strategy Optimization
For each ticker, tests all strategies and selects the best one.
Each ticker will run with its own winning strategy for paper trading.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import json
import yfinance as yf
import logging

# Suppress yfinance warnings
logging.getLogger('yfinance').setLevel(logging.ERROR)

# Add the src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.vwap_strategy import VWAPStrategy
from src.strategies.momentum_strategy import MomentumStrategy
from src.strategies.breakout_strategy import BreakoutStrategy
from src.strategies.mean_reversion import MeanReversionStrategy

# Configuration
INITIAL_CAPITAL = 100000.0
COMMISSION = 0.001  # 0.1%
SLIPPAGE = 0.0005   # 0.05%

# User's requested tickers - focused list
TICKERS = [
    'AMD',    # AMD
    'TSLA',   # Tesla
    'MSFT',   # Microsoft
    'AAPL',   # Apple
    'AVGO',   # Broadcom
    'ARM',    # ARM Holdings
    'NVDA',   # NVIDIA (added - great performer)
    'GOOGL',  # Google (added - great performer)
    'META',   # Meta (added)
    'AMZN',   # Amazon (added)
    'NFLX',   # Netflix (added)
    'CRM',    # Salesforce (added)
]


def fetch_yahoo_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch data directly from Yahoo Finance with proper timezone handling."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)

        if df.empty:
            return pd.DataFrame()

        # Rename columns to lowercase
        df.columns = [col.lower() for col in df.columns]

        # Remove timezone info to avoid comparison issues
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        return df[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()


def get_strategies():
    """Return list of all strategies with default parameters."""
    return [
        ('SMA_Crossover', SMACrossoverStrategy(short_window=50, long_window=200)),
        ('RSI', RSIStrategy(period=14, oversold=30, overbought=70)),
        ('MACD', MACDStrategy(fast_period=12, slow_period=26, signal_period=9)),
        ('Bollinger_Bands', BollingerBandsStrategy(period=20, num_std=2.0)),
        ('VWAP', VWAPStrategy(period=20)),
        ('Momentum', MomentumStrategy(period=20, threshold=0.0)),
        ('Breakout', BreakoutStrategy(lookback_period=20, breakout_threshold=0.02)),
        ('Mean_Reversion', MeanReversionStrategy(period=20, entry_threshold=2.0, exit_threshold=0.5)),
    ]


def simulate_trading(data: pd.DataFrame, signals: pd.Series,
                     initial_capital: float, commission: float, slippage: float) -> Dict:
    """Simulate trading based on signals."""

    cash = initial_capital
    position = 0
    portfolio_value = []
    trades = []

    entry_price = None
    entry_date = None

    for date, row in data.iterrows():
        if date not in signals.index:
            portfolio_value.append(cash + (position * row['close']))
            continue

        signal = signals.loc[date]
        if isinstance(signal, pd.Series):
            signal = signal.iloc[0]
        current_price = row['close']

        # BUY signal
        if signal == 1 and position == 0:
            shares_to_buy = int(cash / (current_price * (1 + commission + slippage)))

            if shares_to_buy > 0:
                cost = shares_to_buy * current_price * (1 + commission + slippage)

                if cost <= cash:
                    position = shares_to_buy
                    cash -= cost
                    entry_price = current_price
                    entry_date = date

        # SELL signal
        elif signal == -1 and position > 0:
            proceeds = position * current_price * (1 - commission - slippage)
            profit = proceeds - (position * entry_price * (1 + commission + slippage))
            profit_pct = (profit / (position * entry_price)) * 100

            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': current_price,
                'shares': position,
                'profit': profit,
                'profit_pct': profit_pct
            })

            cash += proceeds
            position = 0
            entry_price = None
            entry_date = None

        portfolio_value.append(cash + (position * current_price))

    # Close open position at end
    if position > 0 and len(data) > 0:
        final_price = data.iloc[-1]['close']
        proceeds = position * final_price * (1 - commission - slippage)
        profit = proceeds - (position * entry_price * (1 + commission + slippage))
        profit_pct = (profit / (position * entry_price)) * 100

        trades.append({
            'entry_date': entry_date,
            'exit_date': data.index[-1],
            'entry_price': entry_price,
            'exit_price': final_price,
            'shares': position,
            'profit': profit,
            'profit_pct': profit_pct
        })

        cash += proceeds
        position = 0

    equity_curve = pd.Series(portfolio_value, index=data.index[:len(portfolio_value)])

    return {
        'trades': trades,
        'equity_curve': equity_curve,
        'final_value': cash
    }


def calculate_metrics(equity_curve: pd.Series, trades: List, initial_capital: float) -> Dict:
    """Calculate performance metrics."""

    if equity_curve is None or len(equity_curve) == 0:
        return None

    final_value = equity_curve.iloc[-1]
    total_return = (final_value / initial_capital) - 1

    # Daily returns
    daily_returns = equity_curve.pct_change().dropna()

    # Sharpe ratio (annualized)
    if len(daily_returns) > 0 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    else:
        sharpe = 0

    # Max drawdown
    cumulative_max = equity_curve.expanding().max()
    drawdown = (equity_curve - cumulative_max) / cumulative_max
    max_dd = abs(drawdown.min()) if len(drawdown) > 0 else 0

    # Trade statistics
    if len(trades) > 0:
        profits = [t['profit'] for t in trades]
        winning_trades = sum(1 for p in profits if p > 0)
        losing_trades = sum(1 for p in profits if p < 0)
        win_rate = winning_trades / len(trades) if len(trades) > 0 else 0

        gross_profit = sum(p for p in profits if p > 0)
        gross_loss = abs(sum(p for p in profits if p < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
    else:
        winning_trades = 0
        losing_trades = 0
        win_rate = 0
        profit_factor = 0

    return {
        'total_return_pct': total_return * 100,
        'sharpe_ratio': sharpe,
        'max_drawdown_pct': max_dd * 100,
        'win_rate_pct': win_rate * 100,
        'profit_factor': profit_factor,
        'total_trades': len(trades),
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'final_value': final_value
    }


def run_single_backtest(strategy, strategy_name: str, ticker: str,
                        data: pd.DataFrame) -> Dict[str, Any]:
    """Run a single backtest and return results."""
    try:
        if data is None or data.empty:
            return {
                'strategy': strategy_name,
                'ticker': ticker,
                'success': False,
                'error': 'No data available'
            }

        # Generate signals
        signals = strategy.generate_signals(data)

        # Simulate trading
        sim_results = simulate_trading(
            data=data,
            signals=signals,
            initial_capital=INITIAL_CAPITAL,
            commission=COMMISSION,
            slippage=SLIPPAGE
        )

        # Calculate metrics
        metrics = calculate_metrics(
            equity_curve=sim_results['equity_curve'],
            trades=sim_results['trades'],
            initial_capital=INITIAL_CAPITAL
        )

        if metrics is None:
            return {
                'strategy': strategy_name,
                'ticker': ticker,
                'success': False,
                'error': 'No metrics calculated'
            }

        return {
            'strategy': strategy_name,
            'ticker': ticker,
            'total_return_pct': metrics['total_return_pct'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown_pct': metrics['max_drawdown_pct'],
            'win_rate_pct': metrics['win_rate_pct'],
            'profit_factor': metrics['profit_factor'],
            'total_trades': metrics['total_trades'],
            'winning_trades': metrics['winning_trades'],
            'losing_trades': metrics['losing_trades'],
            'final_value': metrics['final_value'],
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'strategy': strategy_name,
            'ticker': ticker,
            'total_return_pct': 0,
            'sharpe_ratio': 0,
            'max_drawdown_pct': 0,
            'win_rate_pct': 0,
            'profit_factor': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'final_value': INITIAL_CAPITAL,
            'success': False,
            'error': str(e)
        }


def find_best_strategy_per_ticker(results: List[Dict]) -> Dict[str, Dict]:
    """For each ticker, find the best performing strategy."""

    df = pd.DataFrame(results)
    df_success = df[df['success'] == True].copy()

    if df_success.empty:
        return {}

    # Calculate composite score for each result
    # Score = Sharpe * 0.4 + (Return/100) * 0.3 + (WinRate/100) * 0.2 - (MaxDD/100) * 0.1
    df_success['composite_score'] = (
        df_success['sharpe_ratio'] * 0.40 +
        df_success['total_return_pct'] / 100 * 0.30 +
        df_success['win_rate_pct'] / 100 * 0.20 -
        df_success['max_drawdown_pct'] / 100 * 0.10
    )

    # For each ticker, find the strategy with highest composite score
    best_per_ticker = {}

    for ticker in df_success['ticker'].unique():
        ticker_results = df_success[df_success['ticker'] == ticker]
        best_row = ticker_results.loc[ticker_results['composite_score'].idxmax()]

        best_per_ticker[ticker] = {
            'best_strategy': best_row['strategy'],
            'total_return_pct': best_row['total_return_pct'],
            'sharpe_ratio': best_row['sharpe_ratio'],
            'win_rate_pct': best_row['win_rate_pct'],
            'max_drawdown_pct': best_row['max_drawdown_pct'],
            'total_trades': int(best_row['total_trades']),
            'composite_score': best_row['composite_score'],
            'final_value': best_row['final_value']
        }

    return best_per_ticker


def run_per_ticker_optimization():
    """Run all strategies against all tickers and find best strategy per ticker."""

    # Use last 1 year of data for backtesting
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print("=" * 80)
    print("PER-TICKER STRATEGY OPTIMIZATION")
    print("=" * 80)
    print(f"Period: {start_str} to {end_str}")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"Tickers: {len(TICKERS)}")
    print(f"Strategies: 8")
    print(f"Total Backtests: {len(TICKERS) * 8}")
    print("=" * 80)
    print()

    # Pre-fetch all data
    print("Fetching historical data...")
    ticker_data = {}
    for ticker in TICKERS:
        print(f"  Fetching {ticker}...", end=" ", flush=True)
        data = fetch_yahoo_data(ticker, start_str, end_str)
        if not data.empty:
            ticker_data[ticker] = data
            print(f"{len(data)} rows")
        else:
            print("FAILED")

    print(f"\nLoaded data for {len(ticker_data)} tickers")
    print()

    all_results = []
    strategies = get_strategies()
    total_tests = len(ticker_data) * len(strategies)
    current_test = 0

    for ticker, data in ticker_data.items():
        print(f"\n{'='*60}")
        print(f"Testing {ticker} - Finding Best Strategy")
        print(f"{'='*60}")

        ticker_results = []

        for strategy_name, strategy_class in get_strategies():  # Get fresh instance
            current_test += 1
            print(f"  [{current_test}/{total_tests}] {strategy_name}...", end=" ", flush=True)

            result = run_single_backtest(
                strategy=strategy_class,
                strategy_name=strategy_name,
                ticker=ticker,
                data=data.copy()
            )

            if result['success']:
                print(f"Return: {result['total_return_pct']:+.2f}%, "
                      f"Sharpe: {result['sharpe_ratio']:.2f}, "
                      f"Trades: {result['total_trades']}")
                ticker_results.append(result)
            else:
                print(f"FAILED: {result.get('error', 'Unknown')[:50]}")

            all_results.append(result)

        # Show best for this ticker
        if ticker_results:
            df_ticker = pd.DataFrame(ticker_results)
            df_ticker['score'] = (
                df_ticker['sharpe_ratio'] * 0.40 +
                df_ticker['total_return_pct'] / 100 * 0.30 +
                df_ticker['win_rate_pct'] / 100 * 0.20 -
                df_ticker['max_drawdown_pct'] / 100 * 0.10
            )
            best = df_ticker.loc[df_ticker['score'].idxmax()]
            print(f"\n  >>> BEST for {ticker}: {best['strategy']} "
                  f"(Return: {best['total_return_pct']:+.2f}%, Sharpe: {best['sharpe_ratio']:.2f})")

    return all_results


def analyze_and_create_config(results: List[Dict]) -> Dict[str, Any]:
    """Analyze results and create paper trading configuration."""

    print("\n" + "=" * 80)
    print("PER-TICKER OPTIMIZATION RESULTS")
    print("=" * 80)

    # Find best strategy per ticker
    best_per_ticker = find_best_strategy_per_ticker(results)

    if not best_per_ticker:
        print("No successful backtests!")
        return None

    # Sort by composite score
    sorted_tickers = sorted(
        best_per_ticker.items(),
        key=lambda x: x[1]['composite_score'],
        reverse=True
    )

    print("\n### BEST STRATEGY FOR EACH TICKER ###\n")
    print("Ticker | Best Strategy      | Return % | Sharpe | Win Rate | Max DD | Score")
    print("-" * 85)

    for ticker, data in sorted_tickers:
        print(f"{ticker:6} | {data['best_strategy']:18} | {data['total_return_pct']:+7.2f}% | "
              f"{data['sharpe_ratio']:6.2f} | {data['win_rate_pct']:7.1f}% | "
              f"{data['max_drawdown_pct']:5.1f}% | {data['composite_score']:.3f}")

    # Create paper trading configuration
    print("\n" + "=" * 80)
    print("PAPER TRADING CONFIGURATION")
    print("=" * 80)

    paper_trading_config = []

    for ticker, data in sorted_tickers:
        config = {
            'ticker': ticker,
            'strategy': data['best_strategy'],
            'expected_return': data['total_return_pct'],
            'sharpe_ratio': data['sharpe_ratio'],
            'win_rate': data['win_rate_pct'],
            'allocation_pct': round(100 / len(sorted_tickers), 2)  # Equal allocation
        }
        paper_trading_config.append(config)
        print(f"  {ticker}: {data['best_strategy']} (Expected: {data['total_return_pct']:+.1f}%)")

    # Calculate portfolio statistics
    total_expected_return = sum(c['expected_return'] * c['allocation_pct'] / 100 for c in paper_trading_config)
    avg_sharpe = np.mean([c['sharpe_ratio'] for c in paper_trading_config])
    avg_win_rate = np.mean([c['win_rate'] for c in paper_trading_config])

    print(f"\n  Portfolio Expected Return: {total_expected_return:+.2f}%")
    print(f"  Average Sharpe Ratio: {avg_sharpe:.2f}")
    print(f"  Average Win Rate: {avg_win_rate:.1f}%")

    # Count strategy distribution
    strategy_counts = {}
    for config in paper_trading_config:
        strat = config['strategy']
        strategy_counts[strat] = strategy_counts.get(strat, 0) + 1

    print("\n### STRATEGY DISTRIBUTION ###")
    for strat, count in sorted(strategy_counts.items(), key=lambda x: -x[1]):
        print(f"  {strat}: {count} tickers")

    # Save configuration
    output = {
        'run_date': datetime.now().isoformat(),
        'period': {
            'start': (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
            'end': datetime.now().strftime('%Y-%m-%d')
        },
        'portfolio_stats': {
            'expected_return_pct': total_expected_return,
            'avg_sharpe_ratio': avg_sharpe,
            'avg_win_rate_pct': avg_win_rate,
            'num_tickers': len(paper_trading_config)
        },
        'ticker_strategies': best_per_ticker,
        'paper_trading_config': paper_trading_config,
        'strategy_distribution': strategy_counts,
        'all_backtest_results': [r for r in results if r['success']]
    }

    with open('backtest_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\nConfiguration saved to: backtest_results.json")

    return output


def main():
    print("\n" + "=" * 80)
    print("STARTING PER-TICKER STRATEGY OPTIMIZATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run optimization
    results = run_per_ticker_optimization()

    # Analyze and create config
    config = analyze_and_create_config(results)

    print("\n" + "=" * 80)
    print(f"OPTIMIZATION COMPLETE at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return config


if __name__ == "__main__":
    main()
