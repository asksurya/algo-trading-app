"""
Tests for all centralized enums.

This module tests:
- All enum values are correctly defined
- Enums are proper string enums
- Enums can be created from string values
"""
import pytest

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


class TestTradingEnums:
    """Test suite for trading-related enums."""
    
    def test_signal_type_values(self):
        """Test SignalType enum values."""
        assert SignalType.BUY.value == "buy"
        assert SignalType.SELL.value == "sell"
        assert SignalType.HOLD.value == "hold"
        assert len(list(SignalType)) == 3
    
    def test_signal_type_from_string(self):
        """Test creating SignalType from string."""
        assert SignalType("buy") == SignalType.BUY
        assert SignalType("sell") == SignalType.SELL
        assert SignalType("hold") == SignalType.HOLD
    
    def test_order_side_values(self):
        """Test OrderSideEnum values."""
        assert OrderSideEnum.BUY.value == "buy"
        assert OrderSideEnum.SELL.value == "sell"
        assert len(list(OrderSideEnum)) == 2
    
    def test_order_type_values(self):
        """Test OrderTypeEnum values."""
        assert OrderTypeEnum.MARKET.value == "market"
        assert OrderTypeEnum.LIMIT.value == "limit"
        assert OrderTypeEnum.STOP.value == "stop"
        assert OrderTypeEnum.STOP_LIMIT.value == "stop_limit"
        assert OrderTypeEnum.TRAILING_STOP.value == "trailing_stop"
        assert len(list(OrderTypeEnum)) == 5
    
    def test_order_status_values(self):
        """Test OrderStatusEnum values."""
        expected_statuses = [
            "new", "partially_filled", "filled", "done_for_day",
            "canceled", "expired", "replaced", "pending_cancel",
            "pending_replace", "accepted", "pending_new", "rejected",
            "suspended", "stopped"
        ]
        assert len(list(OrderStatusEnum)) == len(expected_statuses)
        
        for status_value in expected_statuses:
            assert OrderStatusEnum(status_value) is not None
    
    def test_trade_type_values(self):
        """Test TradeType enum values."""
        assert TradeType.BUY.value == "buy"
        assert TradeType.SELL.value == "sell"
        assert len(list(TradeType)) == 2
    
    def test_trade_status_values(self):
        """Test TradeStatus enum values."""
        assert TradeStatus.PENDING.value == "pending"
        assert TradeStatus.FILLED.value == "filled"
        assert TradeStatus.PARTIALLY_FILLED.value == "partially_filled"
        assert TradeStatus.CANCELLED.value == "cancelled"
        assert TradeStatus.REJECTED.value == "rejected"
        assert len(list(TradeStatus)) == 5


class TestUserEnums:
    """Test suite for user-related enums."""
    
    def test_user_role_values(self):
        """Test UserRole enum values."""
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.USER.value == "user"
        assert UserRole.VIEWER.value == "viewer"
        assert len(list(UserRole)) == 3
    
    def test_user_role_is_string_enum(self):
        """Test that UserRole is a string enum."""
        assert isinstance(UserRole.ADMIN, str)
        assert UserRole.ADMIN == "admin"


class TestStrategyEnums:
    """Test suite for strategy-related enums."""
    
    def test_execution_state_values(self):
        """Test ExecutionState enum values."""
        assert ExecutionState.ACTIVE.value == "active"
        assert ExecutionState.INACTIVE.value == "inactive"
        assert ExecutionState.PAUSED.value == "paused"
        assert ExecutionState.ERROR.value == "error"
        assert ExecutionState.CIRCUIT_BREAKER.value == "circuit_breaker"
        assert len(list(ExecutionState)) == 5
    
    def test_live_strategy_status_values(self):
        """Test LiveStrategyStatus enum values."""
        assert LiveStrategyStatus.ACTIVE.value == "active"
        assert LiveStrategyStatus.PAUSED.value == "paused"
        assert LiveStrategyStatus.STOPPED.value == "stopped"
        assert LiveStrategyStatus.ERROR.value == "error"
        assert len(list(LiveStrategyStatus)) == 4
    
    def test_backtest_status_values(self):
        """Test BacktestStatus enum values."""
        assert BacktestStatus.PENDING.value == "pending"
        assert BacktestStatus.RUNNING.value == "running"
        assert BacktestStatus.COMPLETED.value == "completed"
        assert BacktestStatus.FAILED.value == "failed"
        assert BacktestStatus.CANCELLED.value == "cancelled"
        assert len(list(BacktestStatus)) == 5


class TestRiskEnums:
    """Test suite for risk-related enums."""
    
    def test_risk_rule_type_values(self):
        """Test RiskRuleType enum values."""
        expected_types = [
            "max_position_size", "max_daily_loss", "max_drawdown",
            "max_correlation", "max_leverage", "position_limit",
            "sector_limit", "stop_loss", "take_profit"
        ]
        assert len(list(RiskRuleType)) == len(expected_types)
        
        for type_value in expected_types:
            assert RiskRuleType(type_value) is not None
    
    def test_risk_rule_action_values(self):
        """Test RiskRuleAction enum values."""
        assert RiskRuleAction.ALERT.value == "alert"
        assert RiskRuleAction.BLOCK.value == "block"
        assert RiskRuleAction.CLOSE_POSITION.value == "close_position"
        assert RiskRuleAction.CLOSE_ALL.value == "close_all"
        assert RiskRuleAction.REDUCE_SIZE.value == "reduce_size"
        assert len(list(RiskRuleAction)) == 5


class TestNotificationEnums:
    """Test suite for notification-related enums."""
    
    def test_notification_type_values(self):
        """Test NotificationType enum values."""
        expected_types = [
            "order_filled", "order_cancelled", "order_rejected",
            "position_opened", "position_closed", "strategy_signal",
            "risk_breach", "daily_summary", "system_alert",
            "profit_target", "stop_loss"
        ]
        assert len(list(NotificationType)) == len(expected_types)
        
        for type_value in expected_types:
            assert NotificationType(type_value) is not None
    
    def test_notification_channel_values(self):
        """Test NotificationChannel enum values."""
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.IN_APP.value == "in_app"
        assert NotificationChannel.PUSH.value == "push"
        assert NotificationChannel.SMS.value == "sms"
        assert NotificationChannel.WEBHOOK.value == "webhook"
        assert len(list(NotificationChannel)) == 5
    
    def test_notification_priority_values(self):
        """Test NotificationPriority enum values."""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.MEDIUM.value == "medium"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"
        assert len(list(NotificationPriority)) == 4


class TestBrokerEnums:
    """Test suite for broker/API-related enums."""
    
    def test_broker_type_values(self):
        """Test BrokerType enum values."""
        assert BrokerType.ALPACA.value == "alpaca"
        assert BrokerType.INTERACTIVE_BROKERS.value == "interactive_brokers"
        assert BrokerType.TD_AMERITRADE.value == "td_ameritrade"
        assert BrokerType.ROBINHOOD.value == "robinhood"
        assert BrokerType.COINBASE.value == "coinbase"
        assert BrokerType.BINANCE.value == "binance"
        assert len(list(BrokerType)) == 6
    
    def test_api_key_status_values(self):
        """Test ApiKeyStatus enum values."""
        assert ApiKeyStatus.ACTIVE.value == "active"
        assert ApiKeyStatus.INACTIVE.value == "inactive"
        assert ApiKeyStatus.EXPIRED.value == "expired"
        assert ApiKeyStatus.REVOKED.value == "revoked"
        assert len(list(ApiKeyStatus)) == 4


class TestPortfolioEnums:
    """Test suite for portfolio-related enums."""
    
    def test_tax_lot_status_values(self):
        """Test TaxLotStatus enum values."""
        assert TaxLotStatus.OPEN.value == "open"
        assert TaxLotStatus.CLOSED.value == "closed"
        assert TaxLotStatus.PARTIAL.value == "partial"
        assert len(list(TaxLotStatus)) == 3
    
    def test_performance_period_values(self):
        """Test PerformancePeriod enum values."""
        assert PerformancePeriod.DAILY.value == "daily"
        assert PerformancePeriod.WEEKLY.value == "weekly"
        assert PerformancePeriod.MONTHLY.value == "monthly"
        assert PerformancePeriod.QUARTERLY.value == "quarterly"
        assert PerformancePeriod.YEARLY.value == "yearly"
        assert PerformancePeriod.ALL_TIME.value == "all_time"
        assert len(list(PerformancePeriod)) == 6


class TestEnumConsistency:
    """Test suite for enum consistency across the application."""
    
    def test_all_enums_are_string_enums(self):
        """Test that all enums are string enums."""
        all_enums = [
            SignalType.BUY, OrderSideEnum.BUY, OrderTypeEnum.MARKET,
            OrderStatusEnum.NEW, TradeType.BUY, TradeStatus.PENDING,
            UserRole.USER, ExecutionState.ACTIVE, LiveStrategyStatus.ACTIVE,
            BacktestStatus.PENDING, RiskRuleType.MAX_POSITION_SIZE,
            RiskRuleAction.ALERT, NotificationType.ORDER_FILLED,
            NotificationChannel.EMAIL, NotificationPriority.MEDIUM,
            BrokerType.ALPACA, ApiKeyStatus.ACTIVE, TaxLotStatus.OPEN,
            PerformancePeriod.DAILY,
        ]
        
        for enum_value in all_enums:
            assert isinstance(enum_value, str), f"{enum_value} is not a string enum"
    
    def test_enum_values_are_lowercase(self):
        """Test that all enum values are lowercase."""
        all_enums = [
            SignalType, OrderSideEnum, OrderTypeEnum, OrderStatusEnum,
            TradeType, TradeStatus, UserRole, ExecutionState,
            LiveStrategyStatus, BacktestStatus, RiskRuleType,
            RiskRuleAction, NotificationType, NotificationChannel,
            NotificationPriority, BrokerType, ApiKeyStatus,
            TaxLotStatus, PerformancePeriod,
        ]
        
        for enum_class in all_enums:
            for member in enum_class:
                assert member.value == member.value.lower(), \
                    f"{enum_class.__name__}.{member.name} value is not lowercase: {member.value}"
    
    def test_invalid_enum_value_raises_error(self):
        """Test that invalid enum values raise ValueError."""
        with pytest.raises(ValueError):
            SignalType("invalid")
        
        with pytest.raises(ValueError):
            OrderStatusEnum("unknown_status")
        
        with pytest.raises(ValueError):
            UserRole("superadmin")
