"""
Database models package.

This module exports all SQLAlchemy models and enums for use across the application.
All enums are centralized in the enums module to prevent duplicate definitions.
"""

# Import base first
from app.models.base import Base, SoftDeleteMixin, TimestampMixin

# Import centralized enums
from app.models.enums import (
    # Trading enums
    SignalType,
    OrderSideEnum,
    OrderTypeEnum,
    OrderStatusEnum,
    TradeType,
    TradeStatus,
    # User enums
    UserRole,
    # Strategy enums
    ExecutionState,
    LiveStrategyStatus,
    BacktestStatus,
    # Risk enums
    RiskRuleType,
    RiskRuleAction,
    # Notification enums
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    # API/Broker enums
    BrokerType,
    ApiKeyStatus,
    # Portfolio enums
    TaxLotStatus,
    PerformancePeriod,
)

# Import models
from app.models.user import User
from app.models.strategy import Strategy, StrategyTicker
from app.models.trade import Trade, Position
from app.models.order import Order, PositionSnapshot
from app.models.risk_rule import RiskRule
from app.models.notification import Notification, NotificationPreference
from app.models.api_key import ApiKey, ApiKeyAuditLog
from app.models.market_data_cache import MarketDataCache
from app.models.live_strategy import LiveStrategy, SignalHistory
from app.models.backtest import Backtest, BacktestResult, BacktestTrade
from app.models.strategy_execution import StrategyExecution, StrategySignal, StrategyPerformance
from app.models.portfolio import PortfolioSnapshot, PerformanceMetrics, TaxLot
from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade

__all__ = [
    # Base
    "Base",
    # Enums - Trading
    "SignalType",
    "OrderSideEnum",
    "OrderTypeEnum",
    "OrderStatusEnum",
    "TradeType",
    "TradeStatus",
    # Enums - User
    "UserRole",
    # Enums - Strategy
    "ExecutionState",
    "LiveStrategyStatus",
    "BacktestStatus",
    # Enums - Risk
    "RiskRuleType",
    "RiskRuleAction",
    # Enums - Notification
    "NotificationType",
    "NotificationChannel",
    "NotificationPriority",
    # Enums - API/Broker
    "BrokerType",
    "ApiKeyStatus",
    # Enums - Portfolio
    "TaxLotStatus",
    "PerformancePeriod",
    # Models - User
    "User",
    # Models - Strategy
    "Strategy",
    "StrategyTicker",
    # Models - Trading
    "Trade",
    "Position",
    "Order",
    "PositionSnapshot",
    # Models - Risk
    "RiskRule",
    # Models - Notification
    "Notification",
    "NotificationPreference",
    # Models - API
    "ApiKey",
    "ApiKeyAuditLog",
    # Models - Market Data
    "MarketDataCache",
    # Models - Live Trading
    "LiveStrategy",
    "SignalHistory",
    # Models - Backtesting
    "Backtest",
    "BacktestResult",
    "BacktestTrade",
    # Models - Strategy Execution
    "StrategyExecution",
    "StrategySignal",
    "StrategyPerformance",
    # Models - Portfolio Analytics
    "PortfolioSnapshot",
    "PerformanceMetrics",
    "TaxLot",
    # Models - Paper Trading
    "PaperAccount",
    "PaperPosition",
    "PaperTrade",
]
