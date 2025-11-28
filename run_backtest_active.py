"""
Quick Backtest Runner - More Active Strategy
Runs a backtest with shorter SMA windows for more trading signals
"""

import logging
import sys

# Add src to path
sys.path.append('.')

from src.strategies.sma_crossover import SMACrossoverStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_fetcher import DataFetcher


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def run_backtest():
    """Run a sample backtest with more active SMA strategy."""
    print("\n" + "="*60)
    print("BACKTESTING MODE - ACTIVE SMA CROSSOVER STRATEGY (20/50)")
    print("="*60)
    
    # Setup strategy with shorter windows for more signals
    strategy = SMACrossoverStrategy(
        short_window=20,  # Shorter for more trades
        long_window=50
    )
    
    # Backtest parameters
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2024-01-01'
    initial_capital = 100000.0
    
    print(f"Strategy: SMA Crossover (20/50)")
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print("="*60 + "\n")
    
    # Fetch data first using Yahoo Finance (more reliable)
    print("Fetching market data...")
    data_fetcher = DataFetcher(data_provider='yahoo')
    data = data_fetcher.fetch_historical_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        use_cache=False  # Disable cache to avoid issues
    )
    
    if data is None or data.empty:
        print(f"❌ Failed to fetch data for {symbol}")
        print("Please check your internet connection and try again.")
        return None
    
    print(f"✅ Fetched {len(data)} days of market data")
    print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")
    
    # Generate signals using the strategy
    print("\nGenerating trading signals...")
    signals = strategy.generate_signals(data)
    print(f"✅ Generated {len(signals[signals != 0])} trading signals")
    print(f"   - BUY signals: {len(signals[signals == 1])}")
    print(f"   - SELL signals: {len(signals[signals == -1])}")
    
    # Create backtest engine
    print("\nRunning backtest simulation...")
    engine = BacktestEngine(
        strategy=strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        commission=0.001,  # 0.1% commission
        slippage=0.0005     # 0.05% slippage
    )
    
    # Run backtest
    results = engine.run()
    
    # Print results
    print("\n" + "="*60)
    print("BACKTEST RESULTS")
    print("="*60)
    engine.print_results()
    
    # Plot results
    try:
        print("\nGenerating plots...")
        engine.plot_results()
        print("✅ Plots generated successfully!")
    except Exception as e:
        print(f"⚠️  Could not generate plots: {e}")
    
    return results


if __name__ == '__main__':
    setup_logging()
    try:
        results = run_backtest()
        if results and results.get('metrics'):
            print("\n" + "="*60)
            print("📊 PERFORMANCE SUMMARY")
            print("="*60)
            metrics = results['metrics']
            print(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
            print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")
            print(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
            print(f"Total Trades: {metrics.get('total_trades', 0)}")
            print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
            print("="*60)
        print("\n✅ Backtest completed successfully!")
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
