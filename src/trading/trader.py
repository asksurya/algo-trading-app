"""
Live Trading Module

Executes trades in real-time using the Alpaca API.
"""

import pandas as pd
import numpy as np
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    logging.warning("Alpaca SDK not installed. Install with: pip install alpaca-py")

import sys
sys.path.append('../..')

from config.alpaca_config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL
from src.strategies.base_strategy import BaseStrategy
from src.data.data_fetcher import DataFetcher
from src.risk.risk_manager import RiskManager


class LiveTrader:
    """Execute live trading with Alpaca API."""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        symbols: List[str],
        initial_capital: float = 100000,
        update_interval: int = 60,
        paper_trading: bool = True
    ):
        """
        Initialize live trader.
        
        Args:
            strategy: Trading strategy to use
            symbols: List of symbols to trade
            initial_capital: Initial capital (for tracking only)
            update_interval: Seconds between strategy updates
            paper_trading: Use paper trading (True) or live trading (False)
        """
        self.strategy = strategy
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.update_interval = update_interval
        self.paper_trading = paper_trading
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_fetcher = DataFetcher()
        self.risk_manager = RiskManager(initial_capital=initial_capital)
        
        # Trading state
        self.is_running = False
        self.positions = {}
        self.orders = []
        
        # Initialize Alpaca client
        if ALPACA_AVAILABLE:
            try:
                self.trading_client = TradingClient(
                    ALPACA_API_KEY,
                    ALPACA_SECRET_KEY,
                    paper=paper_trading
                )
                self.logger.info(f"Alpaca client initialized ({'PAPER' if paper_trading else 'LIVE'} trading)")
            except Exception as e:
                self.logger.error(f"Failed to initialize Alpaca client: {e}")
                raise
        else:
            raise RuntimeError("Alpaca SDK not available. Install with: pip install alpaca-py")
    
    def start(self):
        """Start live trading."""
        self.logger.info("="*60)
        self.logger.info("STARTING LIVE TRADING")
        self.logger.info("="*60)
        self.logger.info(f"Strategy: {self.strategy}")
        self.logger.info(f"Symbols: {', '.join(self.symbols)}")
        self.logger.info(f"Update Interval: {self.update_interval} seconds")
        self.logger.info(f"Mode: {'PAPER' if self.paper_trading else 'LIVE'} TRADING")
        self.logger.info("="*60)
        
        # Verify account
        self._verify_account()
        
        # Start trading loop
        self.is_running = True
        self._trading_loop()
    
    def stop(self):
        """Stop live trading."""
        self.logger.info("Stopping live trading...")
        self.is_running = False
    
    def _verify_account(self):
        """Verify Alpaca account status."""
        try:
            account = self.trading_client.get_account()
            
            self.logger.info(f"\nAccount Status:")
            self.logger.info(f"  Buying Power: ${float(account.buying_power):,.2f}")
            self.logger.info(f"  Cash: ${float(account.cash):,.2f}")
            self.logger.info(f"  Portfolio Value: ${float(account.portfolio_value):,.2f}")
            self.logger.info(f"  Trading Blocked: {account.trading_blocked}")
            
            if account.trading_blocked:
                raise RuntimeError("Trading is blocked on this account")
            
        except Exception as e:
            self.logger.error(f"Error verifying account: {e}")
            raise
    
    def _trading_loop(self):
        """Main trading loop."""
        while self.is_running:
            try:
                self.logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Processing signals...")
                
                # Check market hours
                if not self._is_market_open():
                    self.logger.info("Market is closed. Waiting...")
                    time.sleep(self.update_interval)
                    continue
                
                # Update positions from Alpaca
                self._update_positions()
                
                # Process each symbol
                for symbol in self.symbols:
                    self._process_symbol(symbol)
                
                # Wait for next update
                self.logger.info(f"Next update in {self.update_interval} seconds...")
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                self.logger.info("\nReceived stop signal")
                self.stop()
                break
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}", exc_info=True)
                time.sleep(self.update_interval)
    
    def _is_market_open(self) -> bool:
        """Check if market is open."""
        try:
            clock = self.trading_client.get_clock()
            return clock.is_open
        except Exception as e:
            self.logger.error(f"Error checking market status: {e}")
            return False
    
    def _update_positions(self):
        """Update positions from Alpaca."""
        try:
            positions = self.trading_client.get_all_positions()
            self.positions = {pos.symbol: int(pos.qty) for pos in positions}
            
            if self.positions:
                self.logger.debug(f"Current positions: {self.positions}")
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def _process_symbol(self, symbol: str):
        """Process trading signals for a symbol."""
        try:
            # Fetch recent data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            data = self.data_fetcher.fetch_historical_data(
                symbol,
                start_date,
                end_date,
                use_cache=False
            )
            
            if data.empty or len(data) < 200:
                self.logger.warning(f"Insufficient data for {symbol}")
                return
            
            # Generate signals
            signals = self.strategy.generate_signals(data)
            latest_signal = signals.iloc[-1]
            current_price = data['close'].iloc[-1]
            
            # Get current position
            current_position = self.positions.get(symbol, 0)
            
            # Log signal
            signal_type = "BUY" if latest_signal == 1 else "SELL" if latest_signal == -1 else "HOLD"
            self.logger.info(f"{symbol}: Signal={signal_type}, Price=${current_price:.2f}, Position={current_position}")
            
            # Execute trades based on signal
            if latest_signal == 1 and current_position == 0:
                # BUY signal
                self._execute_buy(symbol, current_price)
            elif latest_signal == -1 and current_position > 0:
                # SELL signal
                self._execute_sell(symbol, current_position)
            
        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {e}", exc_info=True)
    
    def _execute_buy(self, symbol: str, current_price: float):
        """Execute buy order."""
        try:
            # Get account info
            account = self.trading_client.get_account()
            buying_power = float(account.buying_power)
            
            # Check risk limits
            if not self.risk_manager.can_open_position():
                self.logger.warning(f"Cannot open position for {symbol}: Max positions reached")
                return
            
            # Calculate position size
            max_position_value = self.risk_manager.calculate_position_size(
                current_price,
                buying_power
            )
            
            shares = int(max_position_value / current_price)
            
            if shares < 1:
                self.logger.warning(f"Insufficient buying power for {symbol}")
                return
            
            # Create order
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            order = self.trading_client.submit_order(order_data)
            
            self.logger.info(f"✓ BUY ORDER SUBMITTED: {shares} shares of {symbol} at ${current_price:.2f}")
            self.logger.info(f"  Order ID: {order.id}")
            
            # Update risk manager
            self.risk_manager.add_position(symbol, shares, current_price)
            
        except Exception as e:
            self.logger.error(f"Error executing buy order for {symbol}: {e}")
    
    def _execute_sell(self, symbol: str, shares: int):
        """Execute sell order."""
        try:
            # Create order
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=shares,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            order = self.trading_client.submit_order(order_data)
            
            current_price = self.data_fetcher.get_latest_price(symbol)
            self.logger.info(f"✓ SELL ORDER SUBMITTED: {shares} shares of {symbol} at ${current_price:.2f}")
            self.logger.info(f"  Order ID: {order.id}")
            
            # Update risk manager
            self.risk_manager.remove_position(symbol)
            
        except Exception as e:
            self.logger.error(f"Error executing sell order for {symbol}: {e}")
    
    def get_portfolio_status(self) -> Dict:
        """Get current portfolio status."""
        try:
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            return {
                'equity': float(account.equity),
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'positions': [
                    {
                        'symbol': pos.symbol,
                        'qty': int(pos.qty),
                        'market_value': float(pos.market_value),
                        'avg_entry_price': float(pos.avg_entry_price),
                        'current_price': float(pos.current_price),
                        'unrealized_pl': float(pos.unrealized_pl),
                        'unrealized_plpc': float(pos.unrealized_plpc) * 100
                    }
                    for pos in positions
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio status: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    from src.strategies.sma_crossover import SMACrossoverStrategy
    
    # Initialize strategy
    strategy = SMACrossoverStrategy(short_window=50, long_window=200)
    
    # Initialize trader (paper trading)
    trader = LiveTrader(
        strategy=strategy,
        symbols=['AAPL', 'TSLA'],
        paper_trading=True,
        update_interval=60
    )
    
    # Start trading
    try:
        trader.start()
    except KeyboardInterrupt:
        print("\nStopping trader...")
        trader.stop()
