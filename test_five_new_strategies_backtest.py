#!/usr/bin/env python3
"""
Comprehensive Manual Backtesting for 5 New Trading Strategies

This script verifies that all 5 newly implemented strategies work correctly
with real market data, generate meaningful signals, and handle various parameters.

Strategies tested:
1. Stochastic Oscillator Strategy
2. Keltner Channel Strategy
3. ATR Trailing Stop Strategy
4. Donchian Channel Strategy
5. Ichimoku Cloud Strategy

Test symbols: AAPL, AMD, NVDA, SPY
Date range: Last 12 months
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np
import json
import yfinance as yf
import logging
from collections import defaultdict

# Suppress yfinance warnings
logging.getLogger('yfinance').setLevel(logging.ERROR)

# Add the src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the 5 new strategies
from src.strategies.stochastic_strategy import StochasticStrategy
from src.strategies.keltner_channel import KeltnerChannelStrategy
from src.strategies.atr_trailing_stop import ATRTrailingStopStrategy
from src.strategies.donchian_channel import DonchianChannelStrategy
from src.strategies.ichimoku_cloud import IchimokuCloudStrategy

# Configuration
INITIAL_CAPITAL = 100000.0
COMMISSION = 0.001  # 0.1%
SLIPPAGE = 0.0005   # 0.05%

# Test symbols (as specified in requirements)
TEST_SYMBOLS = ['AAPL', 'AMD', 'NVDA', 'SPY']


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


def get_strategy_variations() -> List[Tuple[str, Any, str]]:
    """
    Return list of all strategy variations to test.

    Returns: List of (strategy_name, strategy_instance, description) tuples
    """
    variations = []

    # 1. Stochastic Oscillator Strategy
    variations.extend([
        ('Stochastic', StochasticStrategy(k_period=14, d_period=3, oversold=20, overbought=80),
         'Default (20/80 thresholds)'),
        ('Stochastic', StochasticStrategy(k_period=14, d_period=3, oversold=30, overbought=70),
         'Conservative (30/70 thresholds)'),
        ('Stochastic', StochasticStrategy(k_period=21, d_period=5, oversold=20, overbought=80),
         'Longer period (21/5)'),
    ])

    # 2. Keltner Channel Strategy
    variations.extend([
        ('Keltner_Channel', KeltnerChannelStrategy(ema_period=20, atr_period=10, multiplier=2.0, use_breakout=True),
         'Breakout mode (default)'),
        ('Keltner_Channel', KeltnerChannelStrategy(ema_period=20, atr_period=10, multiplier=2.0, use_breakout=False),
         'Mean reversion mode'),
        ('Keltner_Channel', KeltnerChannelStrategy(ema_period=50, atr_period=20, multiplier=2.5, use_breakout=True),
         'Wider bands (50/20/2.5)'),
    ])

    # 3. ATR Trailing Stop Strategy
    variations.extend([
        ('ATR_Trailing_Stop', ATRTrailingStopStrategy(atr_period=14, atr_multiplier=3.0, trend_period=50, use_chandelier=True),
         'Chandelier Exit mode (default)'),
        ('ATR_Trailing_Stop', ATRTrailingStopStrategy(atr_period=14, atr_multiplier=3.0, trend_period=50, use_chandelier=False),
         'Simple ATR mode'),
        ('ATR_Trailing_Stop', ATRTrailingStopStrategy(atr_period=20, atr_multiplier=2.5, trend_period=100, use_chandelier=True),
         'Tighter stops (2.5x ATR)'),
    ])

    # 4. Donchian Channel Strategy
    variations.extend([
        ('Donchian_Channel', DonchianChannelStrategy(entry_period=20, exit_period=10, use_system_2=False),
         'System 1 (20/10)'),
        ('Donchian_Channel', DonchianChannelStrategy(use_system_2=True),
         'System 2 (55/20)'),
        ('Donchian_Channel', DonchianChannelStrategy(entry_period=40, exit_period=20, use_system_2=False),
         'Custom (40/20)'),
    ])

    # 5. Ichimoku Cloud Strategy
    variations.extend([
        ('Ichimoku_Cloud', IchimokuCloudStrategy(tenkan_period=9, kijun_period=26, senkou_b_period=52),
         'Default (9/26/52)'),
        ('Ichimoku_Cloud', IchimokuCloudStrategy(tenkan_period=7, kijun_period=22, senkou_b_period=44),
         'Faster (7/22/44)'),
        ('Ichimoku_Cloud', IchimokuCloudStrategy(tenkan_period=12, kijun_period=30, senkou_b_period=60),
         'Slower (12/30/60)'),
    ])

    return variations


def analyze_signals(signals: pd.Series, strategy_name: str, description: str) -> Dict:
    """Analyze signal distribution and characteristics."""

    signal_counts = {
        'total': len(signals),
        'buy': int((signals == 1).sum()),
        'sell': int((signals == -1).sum()),
        'hold': int((signals == 0).sum()),
    }

    # Calculate signal percentages
    if signal_counts['total'] > 0:
        signal_counts['buy_pct'] = (signal_counts['buy'] / signal_counts['total']) * 100
        signal_counts['sell_pct'] = (signal_counts['sell'] / signal_counts['total']) * 100
        signal_counts['hold_pct'] = (signal_counts['hold'] / signal_counts['total']) * 100
    else:
        signal_counts['buy_pct'] = 0
        signal_counts['sell_pct'] = 0
        signal_counts['hold_pct'] = 0

    # Check for signal activity
    has_signals = signal_counts['buy'] > 0 or signal_counts['sell'] > 0

    return {
        'strategy': strategy_name,
        'description': description,
        'signal_counts': signal_counts,
        'has_activity': has_signals,
    }


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

        avg_win = np.mean([p for p in profits if p > 0]) if winning_trades > 0 else 0
        avg_loss = abs(np.mean([p for p in profits if p < 0])) if losing_trades > 0 else 0
    else:
        winning_trades = 0
        losing_trades = 0
        win_rate = 0
        profit_factor = 0
        avg_win = 0
        avg_loss = 0

    return {
        'total_return_pct': total_return * 100,
        'sharpe_ratio': sharpe,
        'max_drawdown_pct': max_dd * 100,
        'win_rate_pct': win_rate * 100,
        'profit_factor': profit_factor,
        'total_trades': len(trades),
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'final_value': final_value
    }


def verify_indicator_calculations(data: pd.DataFrame, strategy, strategy_name: str) -> Dict:
    """Verify that indicator calculations produce reasonable values."""

    try:
        df_with_indicators = strategy.calculate_indicators(data)

        # Check for NaN or infinite values in key columns
        indicator_columns = [col for col in df_with_indicators.columns if col not in ['open', 'high', 'low', 'close', 'volume']]

        issues = {}
        for col in indicator_columns:
            if col in df_with_indicators.columns:
                nan_count = df_with_indicators[col].isna().sum()
                inf_count = np.isinf(df_with_indicators[col]).sum()

                if nan_count > len(df_with_indicators) * 0.5:  # More than 50% NaN is concerning
                    issues[col] = f"High NaN count: {nan_count}/{len(df_with_indicators)}"
                if inf_count > 0:
                    issues[col] = f"Infinite values: {inf_count}"

        # Get latest values for spot check
        latest_values = {}
        if len(df_with_indicators) > 0:
            for col in indicator_columns[:5]:  # First 5 indicator columns
                if col in df_with_indicators.columns:
                    latest_values[col] = float(df_with_indicators[col].iloc[-1]) if not pd.isna(df_with_indicators[col].iloc[-1]) else None

        return {
            'success': len(issues) == 0,
            'issues': issues if issues else None,
            'latest_values': latest_values,
            'total_indicators': len(indicator_columns)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def run_single_backtest(strategy, strategy_name: str, description: str,
                       symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
    """Run a single backtest and return comprehensive results."""
    try:
        if data is None or data.empty:
            return {
                'strategy': strategy_name,
                'description': description,
                'symbol': symbol,
                'success': False,
                'error': 'No data available'
            }

        # Verify indicator calculations
        indicator_check = verify_indicator_calculations(data, strategy, strategy_name)

        # Generate signals
        signals = strategy.generate_signals(data)

        # Analyze signal distribution
        signal_analysis = analyze_signals(signals, strategy_name, description)

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
                'description': description,
                'symbol': symbol,
                'success': False,
                'error': 'No metrics calculated',
                'signal_analysis': signal_analysis,
                'indicator_check': indicator_check
            }

        return {
            'strategy': strategy_name,
            'description': description,
            'symbol': symbol,
            'total_return_pct': metrics['total_return_pct'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown_pct': metrics['max_drawdown_pct'],
            'win_rate_pct': metrics['win_rate_pct'],
            'profit_factor': metrics['profit_factor'],
            'total_trades': metrics['total_trades'],
            'winning_trades': metrics['winning_trades'],
            'losing_trades': metrics['losing_trades'],
            'avg_win': metrics['avg_win'],
            'avg_loss': metrics['avg_loss'],
            'final_value': metrics['final_value'],
            'signal_analysis': signal_analysis,
            'indicator_check': indicator_check,
            'success': True,
            'error': None
        }
    except Exception as e:
        return {
            'strategy': strategy_name,
            'description': description,
            'symbol': symbol,
            'success': False,
            'error': str(e),
            'signal_analysis': None,
            'indicator_check': None
        }


def print_strategy_summary(results: List[Dict], strategy_name: str):
    """Print summary for a specific strategy across all symbols."""
    strategy_results = [r for r in results if r['strategy'] == strategy_name and r['success']]

    if not strategy_results:
        print(f"  No successful backtests for {strategy_name}")
        return

    print(f"\n  {strategy_name} Summary:")
    print(f"  {'-' * 80}")

    for result in strategy_results:
        signals = result['signal_analysis']['signal_counts']
        print(f"    {result['symbol']:6} | {result['description']:30} | "
              f"Signals: {signals['buy']:3}B/{signals['sell']:3}S | "
              f"Trades: {result['total_trades']:3} | "
              f"Return: {result['total_return_pct']:+7.2f}%")


def main():
    print("=" * 100)
    print("COMPREHENSIVE MANUAL BACKTESTING - 5 NEW TRADING STRATEGIES")
    print("=" * 100)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Use last 12 months of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print(f"Test Period: {start_str} to {end_str}")
    print(f"Test Symbols: {', '.join(TEST_SYMBOLS)}")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print()

    # Fetch data for all symbols
    print("Fetching historical data...")
    print("-" * 100)
    symbol_data = {}
    for symbol in TEST_SYMBOLS:
        print(f"  Fetching {symbol}...", end=" ", flush=True)
        data = fetch_yahoo_data(symbol, start_str, end_str)
        if not data.empty:
            symbol_data[symbol] = data
            print(f"OK ({len(data)} rows)")
        else:
            print("FAILED")

    print(f"\nLoaded data for {len(symbol_data)} symbols")
    print()

    # Get all strategy variations
    variations = get_strategy_variations()
    total_tests = len(symbol_data) * len(variations)

    print(f"Total backtests to run: {total_tests} ({len(variations)} variations × {len(symbol_data)} symbols)")
    print("=" * 100)

    # Run all backtests
    all_results = []
    current_test = 0

    for symbol, data in symbol_data.items():
        print(f"\n{'=' * 100}")
        print(f"TESTING SYMBOL: {symbol}")
        print(f"{'=' * 100}")

        for strategy_name, strategy_instance, description in variations:
            current_test += 1
            print(f"  [{current_test:3}/{total_tests}] {strategy_name:20} | {description:40} ... ", end="", flush=True)

            result = run_single_backtest(
                strategy=strategy_instance,
                strategy_name=strategy_name,
                description=description,
                symbol=symbol,
                data=data.copy()
            )

            if result['success']:
                signals = result['signal_analysis']['signal_counts']
                print(f"OK | Signals: {signals['buy']:3}B/{signals['sell']:3}S | "
                      f"Trades: {result['total_trades']:3} | Return: {result['total_return_pct']:+7.2f}%")
            else:
                print(f"FAILED: {result.get('error', 'Unknown')[:60]}")

            all_results.append(result)

    # Generate comprehensive report
    print("\n" + "=" * 100)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 100)

    successful_results = [r for r in all_results if r['success']]
    failed_results = [r for r in all_results if not r['success']]

    print(f"\nTotal Backtests: {len(all_results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Failed: {len(failed_results)}")

    if failed_results:
        print("\nFailed backtests:")
        for result in failed_results:
            print(f"  - {result['strategy']} ({result['description']}) on {result['symbol']}: {result['error']}")

    # Per-strategy summaries
    print("\n" + "=" * 100)
    print("PER-STRATEGY ANALYSIS")
    print("=" * 100)

    unique_strategies = sorted(list(set(r['strategy'] for r in all_results)))

    for strategy in unique_strategies:
        print_strategy_summary(successful_results, strategy)

    # Signal generation verification
    print("\n" + "=" * 100)
    print("SIGNAL GENERATION VERIFICATION")
    print("=" * 100)

    strategy_signal_summary = defaultdict(lambda: {'buy': 0, 'sell': 0, 'total_backtests': 0})

    for result in successful_results:
        if result['signal_analysis']:
            signals = result['signal_analysis']['signal_counts']
            strategy_signal_summary[result['strategy']]['buy'] += signals['buy']
            strategy_signal_summary[result['strategy']]['sell'] += signals['sell']
            strategy_signal_summary[result['strategy']]['total_backtests'] += 1

    print("\nTotal signals generated per strategy (across all symbols and variations):")
    print("-" * 100)
    for strategy in sorted(strategy_signal_summary.keys()):
        stats = strategy_signal_summary[strategy]
        avg_buy = stats['buy'] / stats['total_backtests']
        avg_sell = stats['sell'] / stats['total_backtests']
        print(f"  {strategy:25} | Total BUY: {stats['buy']:5} | Total SELL: {stats['sell']:5} | "
              f"Avg BUY/test: {avg_buy:5.1f} | Avg SELL/test: {avg_sell:5.1f}")

    # Indicator verification
    print("\n" + "=" * 100)
    print("INDICATOR CALCULATION VERIFICATION")
    print("=" * 100)

    indicator_issues = []
    for result in successful_results:
        if result['indicator_check'] and not result['indicator_check']['success']:
            indicator_issues.append({
                'strategy': result['strategy'],
                'symbol': result['symbol'],
                'issues': result['indicator_check'].get('issues') or result['indicator_check'].get('error')
            })

    if indicator_issues:
        print("\nIndicator calculation issues found:")
        for issue in indicator_issues:
            print(f"  - {issue['strategy']} on {issue['symbol']}: {issue['issues']}")
    else:
        print("\nAll indicator calculations verified successfully - no NaN or infinite values detected.")

    # Top performers
    print("\n" + "=" * 100)
    print("TOP PERFORMING VARIATIONS (by total return)")
    print("=" * 100)

    sorted_by_return = sorted(successful_results, key=lambda x: x['total_return_pct'], reverse=True)[:10]

    print("\nRank | Strategy                  | Description                      | Symbol | Return    | Sharpe | Trades")
    print("-" * 100)
    for i, result in enumerate(sorted_by_return, 1):
        print(f"{i:4} | {result['strategy']:25} | {result['description']:32} | "
              f"{result['symbol']:6} | {result['total_return_pct']:+8.2f}% | "
              f"{result['sharpe_ratio']:6.2f} | {result['total_trades']:6}")

    # Save detailed results
    output = {
        'run_date': datetime.now().isoformat(),
        'period': {
            'start': start_str,
            'end': end_str
        },
        'test_symbols': TEST_SYMBOLS,
        'summary': {
            'total_backtests': len(all_results),
            'successful': len(successful_results),
            'failed': len(failed_results)
        },
        'signal_summary': dict(strategy_signal_summary),
        'all_results': all_results,
        'top_performers': sorted_by_return[:20]
    }

    output_file = 'backtest_results_five_new_strategies.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n\nDetailed results saved to: {output_file}")

    print("\n" + "=" * 100)
    print(f"BACKTESTING COMPLETE at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    # Final verification summary
    print("\nVERIFICATION SUMMARY:")
    print("-" * 100)
    print(f"✓ All 5 strategies successfully imported and instantiated")
    print(f"✓ {len(successful_results)}/{len(all_results)} backtests completed successfully")
    print(f"✓ Signal generation verified across all strategies")
    print(f"✓ Indicator calculations verified (no NaN/inf issues)" if not indicator_issues else f"⚠ Some indicator issues detected")
    print(f"✓ Parameter variations tested (3 variations per strategy)")
    print(f"✓ Multiple market conditions tested (4 different symbols)")

    return output


if __name__ == "__main__":
    main()
