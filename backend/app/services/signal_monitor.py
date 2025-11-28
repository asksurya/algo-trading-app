"""
Signal Monitor Service for detecting trading signals in live strategies.

This service monitors market conditions and detects buy/sell signals based on
strategy logic. It works with the StrategyScheduler to enable continuous
automated trading.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import pandas as pd

from app.models import LiveStrategy, SignalHistory, Strategy, SignalType, Order, OrderSideEnum
from app.integrations.alpaca_client import AlpacaClient
from app.services.market_data_cache_service import MarketDataCacheService
from app.strategies.signal_generator import SignalGenerator
from app.services.risk_manager import RiskManager

logger = logging.getLogger(__name__)


class TradingSignal:
    """Represents a detected trading signal."""
    
    def __init__(
        self,
        symbol: str,
        signal_type: SignalType,
        price: float,
        strength: float = 1.0,
        volume: Optional[float] = None,
        indicators: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.symbol = symbol
        self.signal_type = signal_type
        self.price = price
        self.strength = strength
        self.volume = volume
        self.indicators = indicators or {}
        self.timestamp = timestamp or datetime.now(datetime.UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "price": self.price,
            "strength": self.strength,
            "volume": self.volume,
            "indicators": self.indicators,
            "timestamp": self.timestamp.isoformat()
        }


class SignalMonitor:
    """
    Monitors strategies and detects trading signals.
    
    This service runs strategy logic against current market data to detect
    buy/sell signals for automated trading.
    """
    
    def __init__(
        self,
        db: Session,
        alpaca_client: Optional[AlpacaClient] = None,
        market_data_cache: Optional[MarketDataCacheService] = None
    ):
        self.db = db
        self.alpaca_client = alpaca_client
        self.market_data_cache = market_data_cache or MarketDataCacheService(db)
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager(db)
    
    async def check_strategy_signals(
        self,
        live_strategy: LiveStrategy
    ) -> List[TradingSignal]:
        """
        Check a live strategy for new trading signals.
        
        Args:
            live_strategy: The live strategy to check
            
        Returns:
            List of detected trading signals
        """
        try:
            logger.info(f"Checking signals for live strategy {live_strategy.id} ({live_strategy.name})")
            
            # Get strategy configuration
            strategy = self.db.query(Strategy).filter(Strategy.id == live_strategy.strategy_id).first()
            if not strategy:
                logger.error(f"Strategy {live_strategy.strategy_id} not found")
                return []
            
            signals = []
            
            # Check each symbol
            for symbol in live_strategy.symbols:
                signal = await self._check_symbol_signal(
                    live_strategy=live_strategy,
                    strategy=strategy,
                    symbol=symbol
                )
                
                if signal and signal.signal_type != SignalType.HOLD:
                    signals.append(signal)
                    
                    # Record signal in history
                    await self._save_signal_history(live_strategy, signal)
            
            # Update strategy metrics
            live_strategy.last_check = datetime.now(datetime.UTC)
            if signals:
                live_strategy.last_signal = datetime.now(datetime.UTC)
                live_strategy.total_signals += len(signals)
            
            self.db.commit()
            
            logger.info(f"Found {len(signals)} signals for {live_strategy.name}")
            return signals
            
        except Exception as e:
            logger.error(f"Error checking strategy signals: {e}", exc_info=True)
            live_strategy.error_message = str(e)
            self.db.commit()
            return []
    
    async def _check_symbol_signal(
        self,
        live_strategy: LiveStrategy,
        strategy: Strategy,
        symbol: str
    ) -> Optional[TradingSignal]:
        """Check for signal on a specific symbol."""
        try:
            # Get market data
            market_data = await self._get_market_data(symbol, days=60)
            if market_data is None or len(market_data) < 30:
                logger.warning(f"Insufficient data for {symbol}")
                return None
            
            # Get current price
            current_price = market_data['close'].iloc[-1]
            current_volume = market_data['volume'].iloc[-1]
            
            # Check if we already have a position
            has_position = await self._has_open_position(live_strategy, symbol)
            
            # Convert DataFrame to bars list for signal generator
            bars = [
                {
                    'timestamp': row.name,
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                for _, row in market_data.iterrows()
            ]
            
            # Generate signal based on strategy type
            signal_type, strength, reasoning, indicators = self.signal_generator.generate_signal(
                strategy_type=strategy.name,
                parameters=strategy.parameters or {},
                bars=bars,
                has_position=has_position
            )
            
            # Update strategy state for this symbol
            if symbol not in live_strategy.state:
                live_strategy.state[symbol] = {}
            live_strategy.state[symbol].update({
                "last_price": float(current_price),
                "last_check": datetime.now(datetime.UTC).isoformat(),
                "indicators": indicators
            })
            
            if signal_type == SignalType.HOLD:
                return None
            
            # Create trading signal
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                price=float(current_price),
                strength=float(strength),
                volume=float(current_volume),
                indicators=indicators
            )
            
            logger.info(f"Signal detected: {signal_type.value} {symbol} @ ${current_price:.2f} (strength: {strength:.2f})")
            return signal
            
        except Exception as e:
            logger.error(f"Error checking signal for {symbol}: {e}", exc_info=True)
            return None
    
    async def _get_market_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """Get market data for signal analysis."""
        try:
            # Try cache first
            end_date = datetime.now(datetime.UTC).date()
            start_date = end_date - timedelta(days=days)
            
            df = self.market_data_cache.get_cached_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if df is not None and len(df) > 0:
                return df
            
            # If not in cache, fetch from Alpaca
            if self.alpaca_client:
                df = await self.alpaca_client.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is not None and len(df) > 0:
                    # Cache the data
                    self.market_data_cache.cache_data(df, symbol)
                    return df
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return None
    
    async def _has_open_position(self, live_strategy: LiveStrategy, symbol: str) -> bool:
        """Check if there's an open position for this symbol."""
        try:
            # Check for unfilled or filled orders
            open_orders = self.db.query(Order).filter(
                and_(
                    Order.user_id == live_strategy.user_id,
                    Order.symbol == symbol,
                    Order.side == OrderSideEnum.BUY,
                    Order.status.in_(["pending", "filled"])
                )
            ).first()
            
            return open_orders is not None
            
        except Exception as e:
            logger.error(f"Error checking position for {symbol}: {e}")
            return False
    
    async def _save_signal_history(
        self,
        live_strategy: LiveStrategy,
        signal: TradingSignal
    ) -> SignalHistory:
        """Save detected signal to history."""
        try:
            signal_history = SignalHistory(
                live_strategy_id=live_strategy.id,
                symbol=signal.symbol,
                signal_type=signal.signal_type,
                signal_strength=signal.strength,
                price=signal.price,
                volume=signal.volume,
                indicators=signal.indicators,
                timestamp=signal.timestamp
            )
            
            self.db.add(signal_history)
            self.db.commit()
            
            return signal_history
            
        except Exception as e:
            logger.error(f"Error saving signal history: {e}")
            self.db.rollback()
            raise
    
    async def should_execute_signal(
        self,
        signal: TradingSignal,
        live_strategy: LiveStrategy
    ) -> Tuple[bool, Optional[str]]:
        """
        Determine if a signal should trigger trade execution.
        
        Args:
            signal: The trading signal
            live_strategy: The live strategy configuration
            
        Returns:
            Tuple of (should_execute, reason)
        """
        try:
            # Check if auto-execute is enabled
            if not live_strategy.auto_execute:
                return False, "Auto-execute is disabled"
            
            # Check signal strength threshold
            if signal.strength < 0.6:
                return False, f"Signal strength too low: {signal.strength:.2f}"
            
            # Check position limits
            if signal.signal_type == SignalType.BUY:
                if live_strategy.current_positions >= live_strategy.max_positions:
                    return False, f"Max positions reached: {live_strategy.current_positions}/{live_strategy.max_positions}"
            
            # Check daily loss limit
            if live_strategy.daily_loss_limit and live_strategy.daily_pnl < -abs(live_strategy.daily_loss_limit):
                return False, f"Daily loss limit reached: ${live_strategy.daily_pnl:.2f}"
            
            # Validate with risk manager
            is_valid, validation_msg = await self.risk_manager.validate_trade(
                user_id=live_strategy.user_id,
                symbol=signal.symbol,
                side=signal.signal_type.value,
                quantity=1,  # Placeholder, will be calculated later
                price=signal.price
            )
            
            if not is_valid:
                return False, f"Risk validation failed: {validation_msg}"
            
            return True, "All checks passed"
            
        except Exception as e:
            logger.error(f"Error validating signal execution: {e}")
            return False, f"Validation error: {str(e)}"
