"""
Algorithmic Trading Application - Main Entry Point

This is the main entry point for the algorithmic trading application.
It provides a command-line interface for backtesting and live trading.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.append('.')

from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_strategy import RSIStrategy
from src.strategies.macd_strategy import MACDStrategy
from src.backtesting.backtest_engine import BacktestEngine
from src.trading.trader import LiveTrader
from src.utils.visualizer import Visualizer


def setup_logging(level: str = 'INFO'):
    """Setup logging configuration."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def backtest_command(args):
    """Run backtesting."""
    print("\n" + "="*60)
    print("BACKTESTING MODE")
    print("="*60)
    
    # Select strategy
    if args.strategy == 'sma':
        strategy = SMACrossoverStrategy(
            short_window=args.short_window,
            long_window=args.long_window
        )
    elif args.strategy == 'rsi':
        strategy = RSIStrategy(
            period=args.rsi_period,
            oversold=args.oversold,
            overbought=args.overbought
        )
    elif args.strategy == 'macd':
        strategy = MACDStrategy(
            fast_period=args.macd_fast,
            slow_period=args.macd_slow,
            signal_period=args.macd_signal
        )
    else:
        print(f"Unknown strategy: {args.strategy}")
        return
    
    print(f"Strategy: {strategy}")
    print(f"Symbol: {args.symbol}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print("="*60 + "\n")
    
    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        initial_capital=args.capital,
        commission=args.commission,
        slippage=args.slippage
    )
    
    # Run backtest
    results = engine.run()
    
    # Print results
    engine.print_results()
    
    # Plot results if requested
    if args.plot:
        try:
            engine.plot_results()
        except Exception as e:
            print(f"Could not plot results: {e}")


def live_trade_command(args):
    """Run live trading."""
    print("\n" + "="*60)
    print("LIVE TRADING MODE")
    print("="*60)
    
    # Select strategy
    if args.strategy == 'sma':
        strategy = SMACrossoverStrategy(
            short_window=args.short_window,
            long_window=args.long_window
        )
    elif args.strategy == 'rsi':
        strategy = RSIStrategy(
            period=args.rsi_period,
            oversold=args.oversold,
            overbought=args.overbought
        )
    else:
        print(f"Unknown strategy: {args.strategy}")
        return
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(',')]
    
    print(f"Strategy: {strategy}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Update Interval: {args.interval} seconds")
    print(f"Mode: {'PAPER' if args.paper else 'LIVE'} TRADING")
    
    if not args.paper:
        confirm = input("\n⚠️  WARNING: You are about to start LIVE trading with real money!\n"
                       "Type 'YES' to confirm: ")
        if confirm != 'YES':
            print("Live trading cancelled.")
            return
    
    print("="*60 + "\n")
    
    # Create trader
    trader = LiveTrader(
        strategy=strategy,
        symbols=symbols,
        initial_capital=args.capital,
        update_interval=args.interval,
        paper_trading=args.paper
    )
    
    # Start trading
    try:
        trader.start()
    except KeyboardInterrupt:
        print("\n\nStopping trader...")
        trader.stop()
        print("Trading stopped.")


def compare_command(args):
    """Compare multiple strategies."""
    print("\n" + "="*60)
    print("STRATEGY COMPARISON")
    print("="*60)
    
    # Define strategies to compare
    strategies = {
        'SMA(50,200)': SMACrossoverStrategy(short_window=50, long_window=200),
        'SMA(20,50)': SMACrossoverStrategy(short_window=20, long_window=50),
        'RSI(14)': RSIStrategy(period=14, oversold=30, overbought=70),
        'MACD(12,26,9)': MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
    }
    
    print(f"Symbol: {args.symbol}")
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Comparing {len(strategies)} strategies...")
    print("="*60 + "\n")
    
    # Run backtests
    results = {}
    for name, strategy in strategies.items():
        print(f"Testing {name}...")
        engine = BacktestEngine(
            strategy=strategy,
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.capital
        )
        backtest_results = engine.run()
        
        # Only include if we have results
        if backtest_results.get('equity_curve') is not None and len(backtest_results.get('metrics', {})) > 0:
            results[name] = backtest_results['equity_curve']
            
            # Print summary
            metrics = backtest_results['metrics']
            print(f"  Return: {metrics['total_return_pct']:.2f}%")
            print(f"  Sharpe: {metrics['sharpe_ratio']:.3f}")
            print(f"  Max DD: {metrics['max_drawdown_pct']:.2f}%\n")
        else:
            print(f"  ⚠️  No trades generated (insufficient data or no signals)\n")
    
    # Plot comparison
    if args.plot:
        try:
            viz = Visualizer()
            viz.plot_strategy_comparison(results, title=f"Strategy Comparison - {args.symbol}")
        except Exception as e:
            print(f"Could not plot comparison: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Algorithmic Trading Application',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backtest SMA strategy
  python main.py backtest --strategy sma --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01
  
  # Backtest RSI strategy with plots
  python main.py backtest --strategy rsi --symbol TSLA --start-date 2023-01-01 --end-date 2024-01-01 --plot
  
  # Live paper trading
  python main.py live --strategy sma --symbols AAPL,TSLA --paper
  
  # Compare strategies
  python main.py compare --symbol AAPL --start-date 2023-01-01 --end-date 2024-01-01 --plot
        """
    )
    
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run backtesting')
    backtest_parser.add_argument('--strategy', required=True, choices=['sma', 'rsi', 'macd'],
                                help='Trading strategy to use')
    backtest_parser.add_argument('--symbol', required=True, help='Stock symbol (e.g., AAPL)')
    backtest_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--capital', type=float, default=100000,
                                help='Initial capital (default: 100000)')
    backtest_parser.add_argument('--commission', type=float, default=0.001,
                                help='Commission rate (default: 0.001)')
    backtest_parser.add_argument('--slippage', type=float, default=0.0005,
                                help='Slippage rate (default: 0.0005)')
    backtest_parser.add_argument('--short-window', type=int, default=50,
                                help='SMA short window (default: 50)')
    backtest_parser.add_argument('--long-window', type=int, default=200,
                                help='SMA long window (default: 200)')
    backtest_parser.add_argument('--rsi-period', type=int, default=14,
                                help='RSI period (default: 14)')
    backtest_parser.add_argument('--oversold', type=int, default=30,
                                help='RSI oversold threshold (default: 30)')
    backtest_parser.add_argument('--overbought', type=int, default=70,
                                help='RSI overbought threshold (default: 70)')
    backtest_parser.add_argument('--macd-fast', type=int, default=12,
                                help='MACD fast period (default: 12)')
    backtest_parser.add_argument('--macd-slow', type=int, default=26,
                                help='MACD slow period (default: 26)')
    backtest_parser.add_argument('--macd-signal', type=int, default=9,
                                help='MACD signal period (default: 9)')
    backtest_parser.add_argument('--plot', action='store_true',
                                help='Plot results')
    
    # Live trading command
    live_parser = subparsers.add_parser('live', help='Run live trading')
    live_parser.add_argument('--strategy', required=True, choices=['sma', 'rsi'],
                            help='Trading strategy to use')
    live_parser.add_argument('--symbols', required=True,
                            help='Comma-separated list of symbols (e.g., AAPL,TSLA)')
    live_parser.add_argument('--capital', type=float, default=100000,
                            help='Initial capital for tracking (default: 100000)')
    live_parser.add_argument('--interval', type=int, default=60,
                            help='Update interval in seconds (default: 60)')
    live_parser.add_argument('--paper', action='store_true',
                            help='Use paper trading (default: False = live trading)')
    live_parser.add_argument('--short-window', type=int, default=50,
                            help='SMA short window (default: 50)')
    live_parser.add_argument('--long-window', type=int, default=200,
                            help='SMA long window (default: 200)')
    live_parser.add_argument('--rsi-period', type=int, default=14,
                            help='RSI period (default: 14)')
    live_parser.add_argument('--oversold', type=int, default=30,
                            help='RSI oversold threshold (default: 30)')
    live_parser.add_argument('--overbought', type=int, default=70,
                            help='RSI overbought threshold (default: 70)')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple strategies')
    compare_parser.add_argument('--symbol', required=True, help='Stock symbol (e.g., AAPL)')
    compare_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    compare_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    compare_parser.add_argument('--capital', type=float, default=100000,
                               help='Initial capital (default: 100000)')
    compare_parser.add_argument('--plot', action='store_true',
                               help='Plot comparison')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Execute command
    if args.command == 'backtest':
        backtest_command(args)
    elif args.command == 'live':
        live_trade_command(args)
    elif args.command == 'compare':
        compare_command(args)


if __name__ == '__main__':
    main()
