"""
Live Trading Module

Implements live trading with Alpaca API, including:
- Strategy evaluation and selection
- Automated signal generation
- Trade execution
- Position monitoring
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import time

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca SDK not installed for trading")

from src.backtesting.backtest_engine import BacktestEngine
from src.data.data_fetcher import DataFetcher
from src.strategies.base_strategy import BaseStrategy

# Handle both local and Streamlit Cloud deployments
try:
    import streamlit as st
    # Try Streamlit secrets first (for cloud deployment)
    if hasattr(st, 'secrets'):
        ALPACA_API_KEY = st.secrets.get("ALPACA_API_KEY", "")
        ALPACA_SECRET_KEY = st.secrets.get("ALPACA_SECRET_KEY", "")
    else:
        raise ImportError("Streamlit secrets not available")
except (ImportError, FileNotFoundError):
    # Fall back to config file (for local deployment)
    try:
        from config.alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY
    except ImportError:
        # If neither works, use empty strings
        ALPACA_API_KEY = ""
        ALPACA_SECRET_KEY = ""
        logging.warning("No Alpaca credentials found.")


class LiveTrader:
    """Execute live trading based on strategy signals."""
    
    def __init__(
        self,
        strategies: Dict[str, BaseStrategy],
        symbols: List[str],
        initial_capital: float = 10000,
        paper_trading: bool = True,
        risk_per_trade: float = 0.02,
        max_positions: int = 5
    ):
        """
        Initialize Live Trader.
        
        Args:
            strategies: Dictionary of strategy name -> strategy object (will be cloned for each use)
            symbols: List of symbols to trade
            initial_capital: Starting capital
            paper_trading: Use paper trading (True) or live (False)
            risk_per_trade: Max % of capital to risk per trade
            max_positions: Maximum concurrent positions
        """
        self.strategy_templates = strategies  # Store as templates to clone
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.paper_trading = paper_trading
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize Alpaca trading client
        if not ALPACA_AVAILABLE:
            raise ImportError("Alpaca SDK required for live trading. Install: pip install alpaca-py")
        
        self.trading_client = TradingClient(
            ALPACA_API_KEY,
            ALPACA_SECRET_KEY,
            paper=paper_trading
        )
        
        self.data_fetcher = DataFetcher()
        
        # Store best strategy for each symbol
        self.best_strategies = {}
        
        # Track positions
        self.positions = {}
        
        self.logger.info(f"LiveTrader initialized - Paper: {paper_trading}")
    
    def evaluate_strategies(
        self,
        lookback_days: int = 365,
        metric: str = 'sharpe_ratio'
    ) -> Dict[str, Dict]:
        """
        Run backtests to find best strategy for each symbol.
        
        Args:
            lookback_days: Days of historical data for backtest
            metric: Metric to optimize ('sharpe_ratio', 'total_return_pct', 'profit_factor')
        
        Returns:
            Dictionary with best strategy for each symbol
        """
        self.logger.info(f"Evaluating {len(self.strategy_templates)} strategies on {len(self.symbols)} symbols")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        results = {}
        
        for symbol in self.symbols:
            self.logger.info(f"Evaluating strategies for {symbol}")
            
            strategy_results = {}
            best_score = -float('inf')
            best_strategy_name = None
            
            for strategy_name, strategy_template in self.strategy_templates.items():
                try:
                    # Create fresh strategy instance for this backtest
                    # This prevents state pollution between backtests
                    # Simply create a new instance with default parameters
                    strategy = strategy_template.__class__()
                    
                    # Run backtest
                    engine = BacktestEngine(
                        strategy=strategy,
                        symbol=symbol,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        initial_capital=self.initial_capital
                    )
                    
                    backtest_results = engine.run()
                    
                    if backtest_results and backtest_results.get('metrics'):
                        metrics = backtest_results['metrics']
                        score = metrics.get(metric, -float('inf'))
                        
                        strategy_results[strategy_name] = {
                            'metrics': metrics,
                            'score': score
                        }
                        
                        if score > best_score:
                            best_score = score
                            best_strategy_name = strategy_name
                        
                        self.logger.info(f"  {strategy_name}: {metric}={score:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"Error backtesting {strategy_name} on {symbol}: {e}")
            
            if best_strategy_name:
                results[symbol] = {
                    'best_strategy': best_strategy_name,
                    'best_score': best_score,
                    'all_results': strategy_results
                }
                self.best_strategies[symbol] = self.strategy_templates[best_strategy_name]
                self.logger.info(f"✓ Best for {symbol}: {best_strategy_name} ({metric}={best_score:.3f})")
                
                # Log all strategy scores for debugging
                self.logger.debug(f"  All scores for {symbol}:")
                for sname, sresult in sorted(strategy_results.items(), key=lambda x: x[1]['score'], reverse=True):
                    self.logger.debug(f"    {sname}: {sresult['score']:.3f}")
            else:
                self.logger.warning(f"No valid strategies found for {symbol}")
        
        return results
    
    def get_current_signals(self) -> Dict[str, int]:
        """
        Get current trading signals for all symbols.
        
        Returns:
            Dictionary mapping symbol to signal (1=buy, -1=sell, 0=hold)
        """
        signals = {}
        
        # Fetch recent data for signal generation
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)  # Last 60 days for indicators
        
        for symbol in self.symbols:
            if symbol not in self.best_strategies:
                continue
            
            try:
                # Fetch data
                data = self.data_fetcher.fetch_historical_data(
                    symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if data.empty:
                    self.logger.warning(f"No data for {symbol}")
                    continue
                
                # Generate signals
                strategy = self.best_strategies[symbol]
                strategy_signals = strategy.generate_signals(data)
                
                # Get latest signal
                latest_signal = strategy_signals.iloc[-1]
                if isinstance(latest_signal, pd.Series):
                    latest_signal = latest_signal.iloc[0]
                
                signals[symbol] = int(latest_signal)
                
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
        
        return signals
    
    def execute_trades(self, signals: Dict[str, int]) -> List[Dict]:
        """
        Execute trades based on signals.
        
        Args:
            signals: Dictionary of symbol -> signal
        
        Returns:
            List of executed trade details
        """
        executed_trades = []
        
        # Get current account info
        account = self.trading_client.get_account()
        buying_power = float(account.buying_power)
        current_positions = {pos.symbol: pos for pos in self.trading_client.get_all_positions()}
        
        self.logger.info(f"Account buying power: ${buying_power:,.2f}")
        self.logger.info(f"Current positions: {len(current_positions)}")
        
        for symbol, signal in signals.items():
            try:
                has_position = symbol in current_positions
                
                # BUY signal and no position
                if signal == 1 and not has_position:
                    if len(current_positions) >= self.max_positions:
                        self.logger.info(f"Max positions reached, skipping {symbol}")
                        continue
                    
                    # Calculate position size
                    position_value = buying_power * self.risk_per_trade
                    current_price = self.data_fetcher.get_latest_price(symbol)
                    
                    if current_price:
                        qty = int(position_value / current_price)
                        
                        if qty > 0:
                            # Place market buy order
                            order_data = MarketOrderRequest(
                                symbol=symbol,
                                qty=qty,
                                side=OrderSide.BUY,
                                time_in_force=TimeInForce.DAY
                            )
                            
                            order = self.trading_client.submit_order(order_data)
                            
                            executed_trades.append({
                                'symbol': symbol,
                                'action': 'BUY',
                                'qty': qty,
                                'price': current_price,
                                'order_id': order.id,
                                'timestamp': datetime.now()
                            })
                            
                            self.logger.info(f"✓ BUY {qty} {symbol} @ ${current_price:.2f}")
                
                # SELL signal and has position
                elif signal == -1 and has_position:
                    position = current_positions[symbol]
                    qty = abs(int(float(position.qty)))
                    
                    # Place market sell order
                    order_data = MarketOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    )
                    
                    order = self.trading_client.submit_order(order_data)
                    
                    executed_trades.append({
                        'symbol': symbol,
                        'action': 'SELL',
                        'qty': qty,
                        'price': float(position.current_price),
                        'order_id': order.id,
                        'timestamp': datetime.now()
                    })
                    
                    self.logger.info(f"✓ SELL {qty} {symbol} @ ${float(position.current_price):.2f}")
            
            except Exception as e:
                self.logger.error(f"Error executing trade for {symbol}: {e}")
        
        return executed_trades
    
    def run_live_trading(self, check_interval: int = 60):
        """
        Run live trading loop.
        
        Args:
            check_interval: Seconds between signal checks (default: 60)
        """
        self.logger.info("Starting live trading loop...")
        self.logger.info(f"Paper Trading: {self.paper_trading}")
        self.logger.info(f"Symbols: {', '.join(self.symbols)}")
        self.logger.info(f"Check interval: {check_interval} seconds")
        
        try:
            while True:
                self.logger.info(f"\n{'='*50}")
                self.logger.info(f"Checking signals at {datetime.now()}")
                
                # Get signals
                signals = self.get_current_signals()
                
                # Log signals
                for symbol, signal in signals.items():
                    signal_str = "BUY" if signal == 1 else "SELL" if signal == -1 else "HOLD"
                    self.logger.info(f"  {symbol}: {signal_str}")
                
                # Execute trades
                trades = self.execute_trades(signals)
                
                if trades:
                    self.logger.info(f"Executed {len(trades)} trades")
                else:
                    self.logger.info("No trades executed")
                
                # Wait for next check
                self.logger.info(f"Next check in {check_interval} seconds...")
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            self.logger.info("\nLive trading stopped by user")
        except Exception as e:
            self.logger.error(f"Error in live trading loop: {e}")
            raise
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary."""
        try:
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            return {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'positions_count': len(positions),
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'qty': float(pos.qty),
                        'current_price': float(pos.current_price),
                        'market_value': float(pos.market_value),
                        'unrealized_pl': float(pos.unrealized_pl),
                        'unrealized_plpc': float(pos.unrealized_plpc)
                    }
                    for pos in positions
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    from src.strategies.sma_crossover import SMACrossoverStrategy
    from src.strategies.rsi_strategy import RSIStrategy
    from src.strategies.macd_strategy import MACDStrategy
    
    # Create strategies
    strategies = {
        'SMA Crossover': SMACrossoverStrategy(),
        'RSI': RSIStrategy(),
        'MACD': MACDStrategy()
    }
    
    # Create live trader
    trader = LiveTrader(
        strategies=strategies,
        symbols=['AAPL', 'MSFT', 'TSLA'],
        initial_capital=10000,
        paper_trading=True
    )
    
    # Evaluate strategies
    print("\nEvaluating strategies...")
    results = trader.evaluate_strategies(lookback_days=365)
    
    # Get current signals
    print("\nGetting current signals...")
    signals = trader.get_current_signals()
    for symbol, signal in signals.items():
        print(f"{symbol}: {'BUY' if signal == 1 else 'SELL' if signal == -1 else 'HOLD'}")
    
    # Get portfolio summary
    print("\nPortfolio Summary:")
    summary = trader.get_portfolio_summary()
    print(f"Equity: ${summary['equity']:,.2f}")
    print(f"Positions: {summary['positions_count']}")
