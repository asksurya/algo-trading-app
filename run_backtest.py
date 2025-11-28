"""
Quick Backtest Runner
Runs a backtest without importing live trading modules
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
    """Run a sample backtest."""
    print("\n" + "="*60)
    print("BACKTESTING MODE - SMA CROSSOVER STRATEGY")
    print("="*60)
    
    # Setup strategy
    strategy = SMACrossoverStrategy(
        short_window=50,
        long_window=200
    )
    
    # Backtest parameters
    symbol = 'AAPL'
    start_date = '2023-01-01'
    end_date = '2024-01-01'
    initial_capital = 100000.0
    
    print(f"Strategy: {strategy}")
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
    
    # Create backtest engine with Yahoo Finance provider
    # We'll modify it to use the data we already have
    from src.backtesting.backtest_engine import BacktestEngine
    
    # Temporarily monkey-patch to use Yahoo Finance
    import src.data.data_fetcher as df_module
    original_init = df_module.DataFetcher.__init__
    
    def new_init(self, data_provider='yahoo', cache_dir='data'):
        original_init(self, data_provider='yahoo', cache_dir=cache_dir)
    
    df_module.DataFetcher.__init__ = new_init
    
    engine = BacktestEngine(
        strategy=strategy,
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        commission=0.001,
        slippage=0.0005
    )
    
    # Restore original init
    df_module.DataFetcher.__init__ = original_init
    
    # Run backtest
    print("\nRunning backtest simulation...")
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
        print("✅ Plots saved successfully!")
    except Exception as e:
        print(f"⚠️  Could not generate plots: {e}")
    
    return results


if __name__ == '__main__':
    setup_logging()
    try:
        results = run_backtest()
        print("\n✅ Backtest completed successfully!")
    except Exception as e:
        print(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
