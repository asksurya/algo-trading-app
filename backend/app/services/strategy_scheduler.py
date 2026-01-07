"""
Strategy Scheduler Service for automated live trading.

This service schedules and executes live strategy checks in the background,
monitors for trading signals, and automatically executes trades when conditions
are met. It's the core automation engine for Phase 9.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import asyncio
import logging

from app.models import (
    LiveStrategy, LiveStrategyStatus, SignalHistory, SignalType,
    Order, OrderSideEnum, OrderTypeEnum, ApiKey
)
from app.services.signal_monitor import SignalMonitor, TradingSignal
from app.integrations.order_execution import AlpacaOrderExecutor
from app.integrations.alpaca_client import AlpacaClient
from app.services.notification_service import NotificationService
from app.services.encryption_service import EncryptionService
from app.models.notification import NotificationType, NotificationPriority

logger = logging.getLogger(__name__)


class StrategyScheduler:
    """
    Schedules and executes live strategy checks.
    
    This service runs continuously in the background, checking active strategies
    at their configured intervals and executing trades based on detected signals.
    """
    
    def __init__(
        self,
        db: Session,
        alpaca_client: Optional[AlpacaClient] = None,
        order_executor: Optional[AlpacaOrderExecutor] = None
    ):
        self.db = db
        self.alpaca_client = alpaca_client
        self.order_executor = order_executor
        self.signal_monitor = SignalMonitor(db, alpaca_client)
        self.notification_service = NotificationService(db)
        self.running = False
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_monitoring(self):
        """Start the monitoring loop for all active strategies."""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        logger.info("Starting strategy scheduler")

        try:
            while self.running:
                # Get all active strategies
                active_strategies = self.db.query(LiveStrategy).filter(
                    LiveStrategy.status == LiveStrategyStatus.ACTIVE
                ).all()

                logger.info(f"Checking {len(active_strategies)} active strategies")

                # Check each strategy
                for live_strategy in active_strategies:
                    try:
                        # Check if it's time to evaluate this strategy
                        if self._should_check_strategy(live_strategy):
                            await self._check_and_execute_strategy(live_strategy)
                    except Exception as e:
                        logger.error(f"Error checking strategy {live_strategy.id}: {e}", exc_info=True)
                        live_strategy.status = LiveStrategyStatus.ERROR
                        live_strategy.error_message = str(e)
                        self.db.commit()
                
                # Sleep before next check cycle (1 minute)
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
            self.running = False
    
    def stop_monitoring(self):
        """Stop the monitoring loop."""
        logger.info("Stopping strategy scheduler")
        self.running = False
        
        # Cancel all monitoring tasks
        for task_id, task in self._monitoring_tasks.items():
            task.cancel()
        self._monitoring_tasks.clear()
    
    def _should_check_strategy(self, live_strategy: LiveStrategy) -> bool:
        """Determine if a strategy should be checked now."""
        if not live_strategy.last_check:
            return True

        # Ensure last_check is timezone-aware
        last_check = live_strategy.last_check
        if last_check.tzinfo is None:
            # If naive, assume UTC
            last_check = last_check.replace(tzinfo=timezone.utc)

        elapsed = (datetime.now(timezone.utc) - last_check).total_seconds()
        return elapsed >= live_strategy.check_interval
    
    async def _check_and_execute_strategy(self, live_strategy: LiveStrategy):
        """Check a strategy for signals and execute trades if needed."""
        try:
            logger.info(f"Checking strategy {live_strategy.name} (ID: {live_strategy.id})")
            
            # Check for signals
            signals = await self.signal_monitor.check_strategy_signals(live_strategy)
            
            if not signals:
                logger.debug(f"No signals detected for {live_strategy.name}")
                return
            
            logger.info(f"Detected {len(signals)} signals for {live_strategy.name}")
            
            # Process each signal
            for signal in signals:
                await self._process_signal(live_strategy, signal)
            
        except Exception as e:
            logger.error(f"Error checking strategy {live_strategy.id}: {e}", exc_info=True)
            raise
    
    async def _process_signal(
        self,
        live_strategy: LiveStrategy,
        signal: TradingSignal
    ):
        """Process a detected signal and potentially execute a trade."""
        try:
            logger.info(f"Processing signal: {signal.signal_type.value} {signal.symbol} @ ${signal.price:.2f}")
            
            # Check if signal should be executed
            should_execute, reason = await self.signal_monitor.should_execute_signal(
                signal, live_strategy
            )
            
            if not should_execute:
                logger.info(f"Signal not executed: {reason}")
                await self._send_notification(
                    live_strategy,
                    f"Signal detected but not executed: {signal.signal_type.value} {signal.symbol}",
                    f"Reason: {reason}",
                    NotificationPriority.LOW
                )
                return
            
            # Execute the trade
            if live_strategy.auto_execute:
                await self._execute_signal(live_strategy, signal)
            else:
                logger.info(f"Auto-execute disabled, signal logged only")
                await self._send_notification(
                    live_strategy,
                    f"Signal detected: {signal.signal_type.value} {signal.symbol}",
                    f"Price: ${signal.price:.2f}, Strength: {signal.strength:.2f}. Auto-execute is disabled.",
                    NotificationPriority.MEDIUM
                )
        
        except Exception as e:
            logger.error(f"Error processing signal: {e}", exc_info=True)
    
    async def _execute_signal(
        self,
        live_strategy: LiveStrategy,
        signal: TradingSignal
    ):
        """Execute a trade based on a signal."""
        try:
            logger.info(f"Executing trade: {signal.signal_type.value} {signal.symbol}")
            
            # Get user's API key
            user_api_key = self.db.query(ApiKey).filter(
                ApiKey.user_id == live_strategy.user_id
            ).first()
            
            if not user_api_key:
                logger.error(f"No API key found for user {live_strategy.user_id}")
                await self._send_notification(
                    live_strategy,
                    f"Trade execution failed: No API key configured",
                    "Please configure your Alpaca API key in settings",
                    NotificationPriority.HIGH
                )
                return
            
            # Decrypt user's API key
            encryption_service = EncryptionService()
            decrypted_key = encryption_service.decrypt(user_api_key.secret_key)
            
            # Create user-specific order executor
            user_order_executor = AlpacaOrderExecutor(self.db, decrypted_key)
            
            # Calculate position size
            quantity = self._calculate_position_size(
                live_strategy=live_strategy,
                signal=signal
            )
            
            if quantity <= 0:
                logger.warning(f"Invalid quantity calculated: {quantity}")
                return
            
            # Determine order side
            side = OrderSideEnum.BUY if signal.signal_type == SignalType.BUY else OrderSideEnum.SELL
            
            # Place the order with user-specific credentials
            if user_order_executor:
                order = await user_order_executor.place_order(
                    user_id=live_strategy.user_id,
                    symbol=signal.symbol,
                    qty=quantity,
                    side=side.value,
                    order_type=OrderTypeEnum.MARKET.value,
                    time_in_force="day"
                )
                
                if order:
                    # Update signal history with execution details
                    signal_history = self.db.query(SignalHistory).filter(
                        SignalHistory.live_strategy_id == live_strategy.id,
                        SignalHistory.symbol == signal.symbol,
                        SignalHistory.timestamp == signal.timestamp
                    ).first()
                    
                    if signal_history:
                        signal_history.executed = True
                        signal_history.order_id = order.id
                        signal_history.execution_time = datetime.now(timezone.utc)
                        signal_history.execution_price = order.filled_avg_price or signal.price
                    
                    # Update strategy metrics
                    live_strategy.executed_trades += 1
                    if signal.signal_type == SignalType.BUY:
                        live_strategy.current_positions += 1
                    elif signal.signal_type == SignalType.SELL:
                        live_strategy.current_positions = max(0, live_strategy.current_positions - 1)
                    
                    self.db.commit()
                    
                    # Send success notification
                    await self._send_notification(
                        live_strategy,
                        f"Trade executed: {side.value} {quantity} shares of {signal.symbol}",
                        f"Order ID: {order.id}, Price: ${signal.price:.2f}",
                        NotificationPriority.HIGH
                    )
                    
                    logger.info(f"Trade executed successfully: {order.id}")
                else:
                    logger.error("Order execution failed - no order returned")
                    await self._send_notification(
                        live_strategy,
                        f"Trade execution failed: {signal.signal_type.value} {signal.symbol}",
                        "Order placement failed",
                        NotificationPriority.HIGH
                    )
            else:
                logger.warning("No order executor available")
        
        except Exception as e:
            logger.error(f"Error executing signal: {e}", exc_info=True)
            
            # Update signal history with error
            signal_history = self.db.query(SignalHistory).filter(
                SignalHistory.live_strategy_id == live_strategy.id,
                SignalHistory.symbol == signal.symbol,
                SignalHistory.timestamp == signal.timestamp
            ).first()
            
            if signal_history:
                signal_history.execution_error = str(e)
                self.db.commit()
            
            # Send error notification
            await self._send_notification(
                live_strategy,
                f"Trade execution error: {signal.signal_type.value} {signal.symbol}",
                str(e),
                NotificationPriority.HIGH
            )
    
    def _calculate_position_size(
        self,
        live_strategy: LiveStrategy,
        signal: TradingSignal
    ) -> int:
        """
        Calculate the number of shares to trade based on risk parameters.
        
        Uses the position_size_pct parameter to determine position size as a
        percentage of account value.
        """
        try:
            # Get account info if available
            if not self.alpaca_client:
                logger.warning("No Alpaca client available for position sizing")
                return 10  # Default quantity
            
            # For now, use a simple calculation based on max_position_size
            # In production, this should query actual account balance
            if live_strategy.max_position_size:
                quantity = int(live_strategy.max_position_size / signal.price)
            else:
                # Use position_size_pct of assumed portfolio value
                assumed_portfolio = 100000  # $100k default
                position_value = assumed_portfolio * (live_strategy.position_size_pct or 0.02)
                quantity = int(position_value / signal.price)
            
            # Ensure minimum of 1 share
            return max(1, quantity)
        
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 10  # Default fallback
    
    async def _send_notification(
        self,
        live_strategy: LiveStrategy,
        title: str,
        message: str,
        priority: NotificationPriority
    ):
        """Send a notification about strategy activity."""
        try:
            await self.notification_service.create_notification(
                user_id=live_strategy.user_id,
                notification_type=NotificationType.TRADE_EXECUTED,
                title=title,
                message=message,
                priority=priority,
                metadata={
                    "live_strategy_id": live_strategy.id,
                    "strategy_name": live_strategy.name
                }
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def start_strategy(self, live_strategy_id: str) -> bool:
        """Start monitoring a specific strategy."""
        try:
            live_strategy = self.db.query(LiveStrategy).filter(
                LiveStrategy.id == live_strategy_id
            ).first()
            
            if not live_strategy:
                logger.error(f"Strategy {live_strategy_id} not found")
                return False
            
            live_strategy.status = LiveStrategyStatus.ACTIVE
            live_strategy.started_at = datetime.now(timezone.utc)
            live_strategy.stopped_at = None
            live_strategy.error_message = None
            
            self.db.commit()
            
            logger.info(f"Started live strategy: {live_strategy.name}")
            
            # Send notification
            await self._send_notification(
                live_strategy,
                f"Live trading started: {live_strategy.name}",
                f"Monitoring {len(live_strategy.symbols)} symbols with {live_strategy.check_interval}s interval",
                NotificationPriority.MEDIUM
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting strategy: {e}")
            return False
    
    async def stop_strategy(self, live_strategy_id: str) -> bool:
        """Stop monitoring a specific strategy."""
        try:
            live_strategy = self.db.query(LiveStrategy).filter(
                LiveStrategy.id == live_strategy_id
            ).first()
            
            if not live_strategy:
                logger.error(f"Strategy {live_strategy_id} not found")
                return False
            
            live_strategy.status = LiveStrategyStatus.STOPPED
            live_strategy.stopped_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Stopped live strategy: {live_strategy.name}")
            
            # Send notification
            await self._send_notification(
                live_strategy,
                f"Live trading stopped: {live_strategy.name}",
                f"Strategy monitoring has been stopped",
                NotificationPriority.MEDIUM
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error stopping strategy: {e}")
            return False
    
    async def pause_strategy(self, live_strategy_id: str) -> bool:
        """Pause monitoring a specific strategy."""
        try:
            live_strategy = self.db.query(LiveStrategy).filter(
                LiveStrategy.id == live_strategy_id
            ).first()
            
            if not live_strategy:
                logger.error(f"Strategy {live_strategy_id} not found")
                return False
            
            live_strategy.status = LiveStrategyStatus.PAUSED
            self.db.commit()
            
            logger.info(f"Paused live strategy: {live_strategy.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error pausing strategy: {e}")
            return False
    
    def get_strategy_status(self, live_strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a live strategy."""
        try:
            live_strategy = self.db.query(LiveStrategy).filter(
                LiveStrategy.id == live_strategy_id
            ).first()
            
            if not live_strategy:
                return None
            
            # Get recent signals
            recent_signals = self.db.query(SignalHistory).filter(
                SignalHistory.live_strategy_id == live_strategy_id
            ).order_by(SignalHistory.timestamp.desc()).limit(10).all()
            
            return {
                "strategy": live_strategy.to_dict(),
                "recent_signals": [s.to_dict() for s in recent_signals],
                "is_running": live_strategy.status == LiveStrategyStatus.ACTIVE
            }
        
        except Exception as e:
            logger.error(f"Error getting strategy status: {e}")
            return None
