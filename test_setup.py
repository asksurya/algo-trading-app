"""
Quick test to verify application setup
"""

import sys
sys.path.append('.')

print("Testing imports...")

try:
    # Test config imports
    from config.alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY
    print("✓ Config imported successfully")
except Exception as e:
    print(f"✗ Config import failed: {e}")

try:
    # Test data fetcher
    from src.data.data_fetcher import DataFetcher
    print("✓ DataFetcher imported successfully")
except Exception as e:
    print(f"✗ DataFetcher import failed: {e}")

try:
    # Test strategies
    from src.strategies.base_strategy import BaseStrategy
    from src.strategies.sma_crossover import SMACrossoverStrategy
    from src.strategies.rsi_strategy import RSIStrategy
    print("✓ Strategies imported successfully")
except Exception as e:
    print(f"✗ Strategy import failed: {e}")

try:
    # Test backtest engine
    from src.backtesting.backtest_engine import BacktestEngine
    print("✓ BacktestEngine imported successfully")
except Exception as e:
    print(f"✗ BacktestEngine import failed: {e}")

try:
    # Test trader
    from src.trading.trader import LiveTrader
    print("✓ LiveTrader imported successfully")
except Exception as e:
    print(f"✗ LiveTrader import failed: {e}")

try:
    # Test risk manager
    from src.risk.risk_manager import RiskManager
    print("✓ RiskManager imported successfully")
except Exception as e:
    print(f"✗ RiskManager import failed: {e}")

try:
    # Test visualizer
    from src.utils.visualizer import Visualizer
    print("✓ Visualizer imported successfully")
except Exception as e:
    print(f"✗ Visualizer import failed: {e}")

print("\n" + "="*60)
print("Setup verification complete!")
print("="*60)
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Configure Alpaca API keys in config/alpaca_config.py")
print("3. Run a backtest: python main.py backtest --help")
print("4. Try paper trading: python main.py live --help")
