"""
Strategy executor - main orchestrator for automated strategy execution.
Loads strategies, fetches data, generates signals, and executes orders.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid

from app.models.strategy import Strategy
from app.models.strategy_execution import (
    StrategyExecution,
    StrategySignal,
    StrategyPerformance,
    ExecutionState,
    SignalType
)
from app.strategies.signal_generator import SignalGenerator
from app.integrations.market_data import get_market_data_client
from app.integrations.order_execution import get_order_executor
from app.services.order_validation import get_order_validator

logger = logging.getLogger(__name__)


class StrategyExecutionError(Exception):
    """Custom exception for strategy execution errors."""
    pass


class StrategyExecutor:
    """
    Main strategy executor that orchestrates automated trading.
    """
    
    def __init__(self):
        """Initialize strategy executor."""
        self.signal_generator = SignalGenerator()
        self.market_data = get_market_data_client()
        self.order_executor = get_order_executor()
        self.order_validator = get_order_validator()
        logger.info("StrategyExecutor initialized")
    
    async def execute_strategy(
        self,
        strategy: Strategy,
        execution: StrategyExecution,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Execute a single strategy evaluation cycle.
        
        Args:
            strategy: Strategy model
            execution: StrategyExecution model
            db: Database session
            
        Returns:
            Execution result dictionary
        """
        result = {
            'strategy_id': strategy.id,
            'strategy_name': strategy.name,
            'evaluated_at': datetime.now(timezone.utc),
            'signal_generated': False,
            'order_executed': False,
            'error': None
        }
        
        try:
            logger.info(f"Executing strategy: {strategy.name} (ID: {strategy.id})")
            
            # 1. Get symbol to trade
            symbol = self._get_strategy_symbol(strategy)
            if not symbol:
                raise StrategyExecutionError("No symbol configured for strategy")
            
            # 2. Get timeframe from parameters
            timeframe = strategy.parameters.get('timeframe', '1Day')
            
            # 3. Fetch market data
            bars = await self._fetch_market_data(symbol, timeframe, strategy.parameters)
            if not bars or len(bars) < 20:  # Minimum bars for indicators
                raise StrategyExecutionError(f"Insufficient market data for {symbol}")
            
            # 4. Generate signal
            signal_type, signal_strength, reasoning, indicator_values = \
                self.signal_generator.generate_signal(
                    strategy.strategy_type,
                    strategy.parameters,
                    bars,
                    execution.has_open_position
                )
            
            logger.info(f"Generated {signal_type.value} signal for {strategy.name}: {reasoning}")
            
            # 5. Record signal in database
            signal_record = await self._record_signal(
                strategy.id,
                execution.id,
                symbol,
                signal_type,
                signal_strength,
                indicator_values.get('current_price', 0.0),
                indicator_values,
                reasoning,
                db
            )
            
            result['signal_generated'] = True
            result['signal_type'] = signal_type.value
            result['signal_strength'] = signal_strength
            result['reasoning'] = reasoning
            
            # 6. Validate signal against risk management rules
            is_valid, rejection_reason = self.signal_generator.validate_signal(
                signal_type,
                execution.has_open_position,
                execution.trades_today,
                execution.max_trades_per_day,
                execution.loss_today,
                execution.max_loss_per_day,
                execution.consecutive_losses,
                execution.max_consecutive_losses
            )
            
            if not is_valid:
                logger.warning(f"Signal rejected: {rejection_reason}")
                result['rejected'] = True
                result['rejection_reason'] = rejection_reason
                
                # Update signal record
                signal_record.execution_error = rejection_reason
                await db.commit()
                
                return result
            
            # 7. Execute order if not HOLD and not dry run
            if signal_type != SignalType.HOLD and not execution.is_dry_run:
                order_result = await self._execute_order(
                    strategy,
                    execution,
                    symbol,
                    signal_type,
                    indicator_values.get('current_price', 0.0),
                    db
                )
                
                if order_result['success']:
                    result['order_executed'] = True
                    result['order_id'] = order_result['order_id']
                    
                    # Update signal record with order ID
                    signal_record.was_executed = True
                    signal_record.order_id = order_result['order_id']
                    signal_record.executed_at = datetime.now(timezone.utc)
                    
                    # Update execution state
                    await self._update_execution_after_trade(
                        execution,
                        signal_type,
                        order_result.get('filled_qty', 0),
                        order_result.get('filled_price', 0),
                        db
                    )
                else:
                    result['order_error'] = order_result['error']
                    signal_record.execution_error = order_result['error']
            
            elif execution.is_dry_run and signal_type != SignalType.HOLD:
                logger.info(f"Dry run mode: Would execute {signal_type.value} order for {symbol}")
                result['dry_run'] = True
            
            # 8. Update execution state
            execution.last_evaluated_at = datetime.now(timezone.utc)
            if signal_type != SignalType.HOLD:
                execution.last_signal_at = datetime.now(timezone.utc)
            execution.error_count = 0  # Reset error count on success
            execution.last_error = None
            
            await db.commit()
            
            logger.info(f"Strategy execution completed successfully for {strategy.name}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing strategy {strategy.name}: {e}", exc_info=True)
            result['error'] = str(e)
            
            # Update execution error state
            execution.error_count += 1
            execution.last_error = str(e)
            
            # Move to error state if too many consecutive errors
            if execution.error_count >= 5:
                execution.state = ExecutionState.ERROR
                logger.error(f"Strategy {strategy.name} moved to ERROR state after {execution.error_count} errors")
            
            await db.commit()
            return result
    
    def _get_strategy_symbol(self, strategy: Strategy) -> Optional[str]:
        """Extract trading symbol from strategy configuration."""
        # Check parameters for symbol
        symbol = strategy.parameters.get('symbol')
        if symbol:
            return symbol
        
        # Check parameters for ticker (alternative key)
        ticker = strategy.parameters.get('ticker')
        if ticker:
            return ticker
        
        logger.warning(f"No symbol found in strategy {strategy.id} parameters")
        return None
    
    async def _fetch_market_data(
        self,
        symbol: str,
        timeframe: str,
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical market data for strategy evaluation.
        
        Args:
            symbol: Trading symbol
            timeframe: Bar timeframe
            parameters: Strategy parameters
            
        Returns:
            List of bar dictionaries
        """
        try:
            # Determine how many bars to fetch based on strategy needs
            # Most indicators need at least 200 bars for slow SMAs
            limit = parameters.get('lookback_bars', 300)
            
            # Calculate start date based on timeframe
            end = datetime.now(timezone.utc)
            if '1Min' in timeframe or '5Min' in timeframe:
                start = end - timedelta(days=5)  # 5 days for minute bars
            elif '15Min' in timeframe or '30Min' in timeframe:
                start = end - timedelta(days=10)
            elif '1Hour' in timeframe or '4Hour' in timeframe:
                start = end - timedelta(days=30)
            else:
                start = end - timedelta(days=365)  # 1 year for daily bars
            
            bars = await self.market_data.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start,
                end=end,
                limit=limit,
                use_cache=True
            )
            
            logger.info(f"Fetched {len(bars)} bars for {symbol} ({timeframe})")
            return bars
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            raise StrategyExecutionError(f"Failed to fetch market data: {str(e)}")
    
    async def _record_signal(
        self,
        strategy_id: str,
        execution_id: str,
        symbol: str,
        signal_type: SignalType,
        signal_strength: float,
        price: float,
        indicator_values: Dict[str, Any],
        reasoning: str,
        db: AsyncSession
    ) -> StrategySignal:
        """Record signal in database."""
        # Clean indicator values for JSON storage
        clean_indicators = {}
        for key, value in indicator_values.items():
            # Skip pandas Series objects, only store scalar values
            if hasattr(value, 'iloc'):
                continue
            clean_indicators[key] = float(value) if isinstance(value, (int, float)) else value
        
        signal = StrategySignal(
            id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            execution_id=execution_id,
            signal_type=signal_type,
            symbol=symbol,
            signal_strength=signal_strength,
            price_at_signal=price,
            indicator_values=clean_indicators,
            reasoning=reasoning,
            was_executed=False
        )
        
        db.add(signal)
        await db.flush()
        
        return signal
    
    async def _execute_order(
        self,
        strategy: Strategy,
        execution: StrategyExecution,
        symbol: str,
        signal_type: SignalType,
        current_price: float,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Execute trade order via order execution service.
        
        Args:
            strategy: Strategy model
            execution: StrategyExecution model
            symbol: Trading symbol
            signal_type: BUY or SELL
            current_price: Current market price
            db: Database session
            
        Returns:
            Order execution result
        """
        try:
            # Determine order parameters
            side = "buy" if signal_type == SignalType.BUY else "sell"
            
            # Get quantity from strategy parameters
            qty = None
            notional = None
            
            if 'quantity' in strategy.parameters:
                qty = float(strategy.parameters['quantity'])
            elif 'notional' in strategy.parameters:
                notional = float(strategy.parameters['notional'])
            else:
                # Default: use $1000 notional
                notional = 1000.0
            
            # For SELL orders, use current position quantity
            if signal_type == SignalType.SELL and execution.has_open_position:
                qty = execution.current_position_qty
                notional = None
            
            # Validate order
            validation_result = await self.order_validator.validate_order(
                symbol=symbol,
                qty=qty,
                notional=notional,
                side=side,
                order_type='market'
            )
            
            if not validation_result['valid']:
                error_msg = f"Order validation failed: {validation_result.get('warnings', [])}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
            
            # Execute order
            logger.info(f"Executing {side.upper()} order for {symbol}, qty={qty}, notional={notional}")
            
            order = await self.order_executor.place_order(
                symbol=symbol,
                qty=qty,
                notional=notional,
                side=side,
                order_type='market',
                time_in_force='day'
            )
            
            logger.info(f"Order executed successfully: {order['id']}")
            
            return {
                'success': True,
                'order_id': order['id'],
                'filled_qty': order.get('filled_qty', qty or 0),
                'filled_price': order.get('filled_avg_price', current_price)
            }
            
        except Exception as e:
            logger.error(f"Error executing order: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    async def _update_execution_after_trade(
        self,
        execution: StrategyExecution,
        signal_type: SignalType,
        filled_qty: float,
        filled_price: float,
        db: AsyncSession
    ) -> None:
        """Update execution state after a trade is executed."""
        execution.last_trade_at = datetime.now(timezone.utc)
        execution.trades_today += 1
        
        if signal_type == SignalType.BUY:
            execution.has_open_position = True
            execution.current_position_qty = filled_qty
            execution.current_position_entry_price = filled_price
        elif signal_type == SignalType.SELL:
            # Calculate P&L
            if execution.current_position_entry_price:
                pnl = (filled_price - execution.current_position_entry_price) * execution.current_position_qty
                
                # Update loss tracking
                if pnl < 0:
                    execution.loss_today += abs(pnl)
                    execution.consecutive_losses += 1
                else:
                    execution.consecutive_losses = 0  # Reset on profit
                
                # Check circuit breakers
                if execution.loss_today >= execution.max_loss_per_day:
                    execution.state = ExecutionState.CIRCUIT_BREAKER
                    logger.warning(f"Circuit breaker triggered: max loss per day reached")
                
                if execution.consecutive_losses >= execution.max_consecutive_losses:
                    execution.state = ExecutionState.CIRCUIT_BREAKER
                    logger.warning(f"Circuit breaker triggered: max consecutive losses reached")
            
            # Close position
            execution.has_open_position = False
            execution.current_position_qty = None
            execution.current_position_entry_price = None
        
        # Check if max trades per day reached
        if execution.trades_today >= execution.max_trades_per_day:
            execution.state = ExecutionState.CIRCUIT_BREAKER
            logger.warning(f"Circuit breaker triggered: max trades per day reached")
    
    async def load_active_strategies(self, db: AsyncSession) -> List[Tuple[Strategy, StrategyExecution]]:
        """
        Load all active strategies with their execution state.
        
        Args:
            db: Database session
            
        Returns:
            List of (Strategy, StrategyExecution) tuples
        """
        try:
            # Query active strategy executions
            stmt = select(StrategyExecution).where(
                StrategyExecution.state == ExecutionState.ACTIVE
            )
            result = await db.execute(stmt)
            executions = result.scalars().all()
            
            strategies_with_executions = []
            
            for execution in executions:
                # Load associated strategy
                stmt = select(Strategy).where(Strategy.id == execution.strategy_id)
                result = await db.execute(stmt)
                strategy = result.scalar_one_or_none()
                
                if strategy:
                    strategies_with_executions.append((strategy, execution))
                else:
                    logger.warning(f"Strategy {execution.strategy_id} not found for active execution")
            
            logger.info(f"Loaded {len(strategies_with_executions)} active strategies")
            return strategies_with_executions
            
        except Exception as e:
            logger.error(f"Error loading active strategies: {e}")
            return []
    
    async def reset_daily_counters(self, db: AsyncSession) -> None:
        """
        Reset daily counters for all strategy executions.
        Should be called at market open each day.
        """
        try:
            stmt = update(StrategyExecution).values(
                trades_today=0,
                loss_today=0.0
            )
            await db.execute(stmt)
            await db.commit()
            
            logger.info("Reset daily counters for all strategy executions")
            
        except Exception as e:
            logger.error(f"Error resetting daily counters: {e}")
            await db.rollback()