"""Consolidated initial schema migration

This migration consolidates all previous migrations into a single,
properly ordered initial schema that matches the current models.

Revision ID: consolidated_001
Revises:
Create Date: 2025-12-10

IMPORTANT: This migration replaces all previous migrations.
Before running this, ensure your database is empty or has been reset.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'consolidated_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables in proper dependency order."""
    
    # =========================================================================
    # Core Tables (no dependencies)
    # =========================================================================
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', sa.Enum('admin', 'user', 'viewer', name='userrole'), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'])
    
    # Market Data Cache (no FK dependencies)
    op.create_table(
        'market_data_cache',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), server_default='alpaca'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.UniqueConstraint('symbol', 'date', name='uix_symbol_date'),
    )
    op.create_index('idx_market_data_symbol', 'market_data_cache', ['symbol'])
    op.create_index('idx_market_data_date', 'market_data_cache', ['date'])
    op.create_index('idx_symbol_date_range', 'market_data_cache', ['symbol', 'date'])
    
    # =========================================================================
    # User-dependent Tables
    # =========================================================================
    
    # Strategies
    op.create_table(
        'strategies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', sa.String(100), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_backtested', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('backtest_results', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_strategies_id', 'strategies', ['id'])
    op.create_index('ix_strategies_user_id', 'strategies', ['user_id'])
    
    # Strategy Tickers
    op.create_table(
        'strategy_tickers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('allocation_percent', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_strategy_tickers_strategy_id', 'strategy_tickers', ['strategy_id'])
    op.create_index('ix_strategy_tickers_ticker', 'strategy_tickers', ['ticker'])
    
    # Trades
    op.create_table(
        'trades',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('trade_type', sa.Enum('buy', 'sell', name='tradetype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'filled', 'partially_filled', 'cancelled', 'rejected', name='tradestatus'), nullable=False, server_default='pending'),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('filled_quantity', sa.Numeric(precision=18, scale=8), nullable=False, server_default='0'),
        sa.Column('price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('filled_avg_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('order_id', sa.String(100), nullable=True),
        sa.Column('realized_pnl', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_trades_id', 'trades', ['id'])
    op.create_index('ix_trades_user_id', 'trades', ['user_id'])
    op.create_index('ix_trades_strategy_id', 'trades', ['strategy_id'])
    op.create_index('ix_trades_ticker', 'trades', ['ticker'])
    
    # Positions
    op.create_table(
        'positions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('avg_entry_price', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('unrealized_pnl', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('realized_pnl', sa.Numeric(precision=18, scale=8), nullable=False, server_default='0'),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_positions_id', 'positions', ['id'])
    op.create_index('ix_positions_user_id', 'positions', ['user_id'])
    op.create_index('ix_positions_strategy_id', 'positions', ['strategy_id'])
    op.create_index('ix_positions_ticker', 'positions', ['ticker'])
    
    # Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alpaca_order_id', sa.String(100), nullable=False, unique=True),
        sa.Column('client_order_id', sa.String(100), nullable=True),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('side', sa.Enum('buy', 'sell', name='ordersideenum'), nullable=False),
        sa.Column('order_type', sa.Enum('market', 'limit', 'stop', 'stop_limit', 'trailing_stop', name='ordertypeenum'), nullable=False),
        sa.Column('time_in_force', sa.String(10), nullable=False),
        sa.Column('qty', sa.Float(), nullable=True),
        sa.Column('notional', sa.Float(), nullable=True),
        sa.Column('filled_qty', sa.Float(), nullable=False, server_default='0'),
        sa.Column('limit_price', sa.Float(), nullable=True),
        sa.Column('stop_price', sa.Float(), nullable=True),
        sa.Column('filled_avg_price', sa.Float(), nullable=True),
        sa.Column('trail_price', sa.Float(), nullable=True),
        sa.Column('trail_percent', sa.Float(), nullable=True),
        sa.Column('hwm', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('new', 'partially_filled', 'filled', 'done_for_day', 'canceled', 'expired', 'replaced', 'pending_cancel', 'pending_replace', 'accepted', 'pending_new', 'rejected', 'suspended', 'stopped', name='orderstatusenum'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_by', sa.String(100), nullable=True),
        sa.Column('replaces', sa.String(100), nullable=True),
        sa.Column('extended_hours', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('asset_class', sa.String(20), nullable=False, server_default='us_equity'),
        sa.Column('asset_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_orders_id', 'orders', ['id'])
    op.create_index('ix_orders_alpaca_order_id', 'orders', ['alpaca_order_id'], unique=True)
    op.create_index('ix_orders_symbol', 'orders', ['symbol'])
    op.create_index('ix_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_user_created', 'orders', ['user_id', 'created_at'])
    op.create_index('idx_orders_symbol_created', 'orders', ['symbol', 'created_at'])
    op.create_index('idx_orders_status_created', 'orders', ['status', 'created_at'])
    op.create_index('idx_orders_user_symbol', 'orders', ['user_id', 'symbol'])
    
    # Position Snapshots
    op.create_table(
        'position_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('side', sa.Enum('buy', 'sell', name='ordersideenum'), nullable=False),
        sa.Column('avg_entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('market_value', sa.Float(), nullable=False),
        sa.Column('cost_basis', sa.Float(), nullable=False),
        sa.Column('unrealized_pl', sa.Float(), nullable=False),
        sa.Column('unrealized_plpc', sa.Float(), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_position_snapshots_user_time', 'position_snapshots', ['user_id', 'snapshot_at'])
    op.create_index('idx_position_snapshots_symbol_time', 'position_snapshots', ['symbol', 'snapshot_at'])
    
    # Risk Rules
    op.create_table(
        'risk_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.Enum('max_position_size', 'max_daily_loss', 'max_drawdown', 'max_correlation', 'max_leverage', 'position_limit', 'sector_limit', 'stop_loss', 'take_profit', name='riskruletype'), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('threshold_unit', sa.String(20), nullable=False, server_default='percent'),
        sa.Column('action', sa.Enum('alert', 'block', 'close_position', 'close_all', 'reduce_size', name='riskruleaction'), nullable=False, server_default='alert'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('breach_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_breach_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_risk_rules_id', 'risk_rules', ['id'])
    op.create_index('ix_risk_rules_user_id', 'risk_rules', ['user_id'])
    op.create_index('ix_risk_rules_strategy_id', 'risk_rules', ['strategy_id'])
    
    # Notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.Enum('order_filled', 'order_cancelled', 'order_rejected', 'position_opened', 'position_closed', 'strategy_signal', 'risk_breach', 'daily_summary', 'system_alert', 'profit_target', 'stop_loss', name='notificationtype'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'urgent', name='notificationpriority'), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('strategy_id', sa.String(36), nullable=True),
        sa.Column('order_id', sa.String(36), nullable=True),
        sa.Column('trade_id', sa.String(36), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_via', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_notifications_id', 'notifications', ['id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    
    # Notification Preferences
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('notification_type', sa.Enum('order_filled', 'order_cancelled', 'order_rejected', 'position_opened', 'position_closed', 'strategy_signal', 'risk_breach', 'daily_summary', 'system_alert', 'profit_target', 'stop_loss', name='notificationtype'), nullable=False),
        sa.Column('channel', sa.Enum('email', 'in_app', 'push', 'sms', 'webhook', name='notificationchannel'), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('min_priority', sa.Enum('low', 'medium', 'high', 'urgent', name='notificationpriority'), nullable=False, server_default='low'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quiet_start_hour', sa.Integer(), nullable=True),
        sa.Column('quiet_end_hour', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('webhook_url', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_notification_preferences_id', 'notification_preferences', ['id'])
    op.create_index('ix_notification_preferences_user_id', 'notification_preferences', ['user_id'])
    
    # API Keys
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('broker', sa.Enum('alpaca', 'interactive_brokers', 'td_ameritrade', 'robinhood', 'coinbase', 'binance', name='brokertype'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('encrypted_api_secret', sa.Text(), nullable=False),
        sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('account_id', sa.String(255), nullable=True),
        sa.Column('base_url', sa.String(512), nullable=True),
        sa.Column('is_paper_trading', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.Enum('active', 'inactive', 'expired', 'revoked', name='apikeystatus'), nullable=False, server_default='active'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rotation_history', sa.Text(), nullable=True),
        sa.Column('last_rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_api_keys_id', 'api_keys', ['id'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_broker', 'api_keys', ['broker'])
    
    # API Key Audit Logs
    op.create_table(
        'api_key_audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('api_key_id', sa.String(36), sa.ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_api_key_audit_logs_id', 'api_key_audit_logs', ['id'])
    op.create_index('ix_api_key_audit_logs_api_key_id', 'api_key_audit_logs', ['api_key_id'])
    op.create_index('ix_api_key_audit_logs_user_id', 'api_key_audit_logs', ['user_id'])
    op.create_index('ix_api_key_audit_logs_action', 'api_key_audit_logs', ['action'])
    op.create_index('ix_api_key_audit_logs_created_at', 'api_key_audit_logs', ['created_at'])
    
    # =========================================================================
    # Strategy Execution Tables
    # =========================================================================
    
    # Strategy Executions
    op.create_table(
        'strategy_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('state', sa.Enum('active', 'inactive', 'paused', 'error', 'circuit_breaker', name='executionstate'), nullable=False, server_default='inactive'),
        sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_signal_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_trade_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trades_today', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_trades_per_day', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('loss_today', sa.Float(), nullable=False, server_default='0'),
        sa.Column('max_loss_per_day', sa.Float(), nullable=False, server_default='1000'),
        sa.Column('consecutive_losses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_consecutive_losses', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('circuit_breaker_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('has_open_position', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('current_position_qty', sa.Float(), nullable=True),
        sa.Column('current_position_entry_price', sa.Float(), nullable=True),
        sa.Column('config_overrides', sa.JSON(), nullable=True),
        sa.Column('is_dry_run', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_strategy_executions_id', 'strategy_executions', ['id'])
    op.create_index('ix_strategy_executions_strategy_id', 'strategy_executions', ['strategy_id'])
    op.create_index('ix_strategy_executions_state', 'strategy_executions', ['state'])
    
    # Strategy Signals
    op.create_table(
        'strategy_signals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('execution_id', sa.String(36), sa.ForeignKey('strategy_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('signal_type', sa.Enum('buy', 'sell', 'hold', name='signaltype'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('signal_strength', sa.Float(), nullable=True),
        sa.Column('price_at_signal', sa.Float(), nullable=False),
        sa.Column('indicator_values', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('was_executed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_id', sa.String(36), nullable=True),
        sa.Column('execution_error', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_strategy_signals_id', 'strategy_signals', ['id'])
    op.create_index('ix_strategy_signals_strategy_id', 'strategy_signals', ['strategy_id'])
    op.create_index('ix_strategy_signals_execution_id', 'strategy_signals', ['execution_id'])
    op.create_index('ix_strategy_signals_signal_type', 'strategy_signals', ['signal_type'])
    op.create_index('ix_strategy_signals_symbol', 'strategy_signals', ['symbol'])
    op.create_index('ix_strategy_signals_generated_at', 'strategy_signals', ['generated_at'])
    
    # Strategy Performance
    op.create_table(
        'strategy_performance',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False, server_default='daily'),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winning_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losing_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default='0'),
        sa.Column('gross_profit', sa.Float(), nullable=False, server_default='0'),
        sa.Column('gross_loss', sa.Float(), nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('profit_factor', sa.Float(), nullable=True),
        sa.Column('avg_win', sa.Float(), nullable=True),
        sa.Column('avg_loss', sa.Float(), nullable=True),
        sa.Column('largest_win', sa.Float(), nullable=True),
        sa.Column('largest_loss', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('cumulative_pnl', sa.Float(), nullable=True),
        sa.Column('cumulative_trades', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_strategy_performance_id', 'strategy_performance', ['id'])
    op.create_index('ix_strategy_performance_strategy_id', 'strategy_performance', ['strategy_id'])
    op.create_index('ix_strategy_performance_date', 'strategy_performance', ['date'])
    
    # =========================================================================
    # Live Trading Tables
    # =========================================================================
    
    # Live Strategies
    op.create_table(
        'live_strategies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('symbols', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'stopped', 'error', name='livestrategystatusenum'), nullable=False, server_default='stopped'),
        sa.Column('check_interval', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('auto_execute', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('max_position_size', sa.Float(), nullable=True),
        sa.Column('max_positions', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('daily_loss_limit', sa.Float(), nullable=True),
        sa.Column('position_size_pct', sa.Float(), nullable=True, server_default='0.02'),
        sa.Column('last_check', sa.DateTime(), nullable=True),
        sa.Column('last_signal', sa.DateTime(), nullable=True),
        sa.Column('state', sa.JSON(), server_default='{}'),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('total_signals', sa.Integer(), server_default='0'),
        sa.Column('executed_trades', sa.Integer(), server_default='0'),
        sa.Column('current_positions', sa.Integer(), server_default='0'),
        sa.Column('daily_pnl', sa.Float(), server_default='0'),
        sa.Column('total_pnl', sa.Float(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_live_strategies_id', 'live_strategies', ['id'])
    op.create_index('ix_live_strategies_user_id', 'live_strategies', ['user_id'])
    op.create_index('ix_live_strategies_strategy_id', 'live_strategies', ['strategy_id'])
    op.create_index('ix_live_strategies_status', 'live_strategies', ['status'])
    
    # Signal History
    op.create_table(
        'signal_history',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('live_strategy_id', sa.String(36), sa.ForeignKey('live_strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('signal_type', sa.Enum('buy', 'sell', 'hold', name='signaltype'), nullable=False),
        sa.Column('signal_strength', sa.Float(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('indicators', sa.JSON(), nullable=True),
        sa.Column('executed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('execution_price', sa.Float(), nullable=True),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('execution_time', sa.DateTime(), nullable=True),
        sa.Column('execution_error', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_signal_history_id', 'signal_history', ['id'])
    op.create_index('ix_signal_history_live_strategy_id', 'signal_history', ['live_strategy_id'])
    op.create_index('ix_signal_history_symbol', 'signal_history', ['symbol'])
    op.create_index('ix_signal_history_timestamp', 'signal_history', ['timestamp'])
    
    # =========================================================================
    # Backtesting Tables
    # =========================================================================
    
    # Backtests
    op.create_table(
        'backtests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('initial_capital', sa.Float(), nullable=False, server_default='100000'),
        sa.Column('commission', sa.Float(), nullable=False, server_default='0.001'),
        sa.Column('slippage', sa.Float(), nullable=False, server_default='0.0005'),
        sa.Column('strategy_params', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='backteststatus'), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('winning_trades', sa.Integer(), nullable=True),
        sa.Column('losing_trades', sa.Integer(), nullable=True),
        sa.Column('total_return', sa.Float(), nullable=True),
        sa.Column('total_pnl', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_backtests_id', 'backtests', ['id'])
    op.create_index('ix_backtests_user_id', 'backtests', ['user_id'])
    op.create_index('ix_backtests_strategy_id', 'backtests', ['strategy_id'])
    op.create_index('ix_backtests_status', 'backtests', ['status'])
    op.create_index('ix_backtests_start_date', 'backtests', ['start_date'])
    op.create_index('ix_backtests_end_date', 'backtests', ['end_date'])
    
    # Backtest Results
    op.create_table(
        'backtest_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('backtest_id', sa.String(36), sa.ForeignKey('backtests.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('final_capital', sa.Float(), nullable=False),
        sa.Column('total_return_pct', sa.Float(), nullable=False),
        sa.Column('annualized_return', sa.Float(), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winning_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losing_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=False),
        sa.Column('gross_profit', sa.Float(), nullable=False, server_default='0'),
        sa.Column('gross_loss', sa.Float(), nullable=False, server_default='0'),
        sa.Column('net_profit', sa.Float(), nullable=False),
        sa.Column('profit_factor', sa.Float(), nullable=True),
        sa.Column('avg_trade_pnl', sa.Float(), nullable=False),
        sa.Column('avg_winning_trade', sa.Float(), nullable=True),
        sa.Column('avg_losing_trade', sa.Float(), nullable=True),
        sa.Column('largest_win', sa.Float(), nullable=True),
        sa.Column('largest_loss', sa.Float(), nullable=True),
        sa.Column('max_drawdown_pct', sa.Float(), nullable=False),
        sa.Column('max_drawdown_dollars', sa.Float(), nullable=False),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('sortino_ratio', sa.Float(), nullable=True),
        sa.Column('calmar_ratio', sa.Float(), nullable=True),
        sa.Column('volatility', sa.Float(), nullable=True),
        sa.Column('avg_trade_duration_hours', sa.Float(), nullable=True),
        sa.Column('market_exposure_pct', sa.Float(), nullable=True),
        sa.Column('equity_curve', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('drawdown_periods', sa.JSON(), nullable=True),
        sa.Column('monthly_returns', sa.JSON(), nullable=True),
        sa.Column('additional_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_backtest_results_id', 'backtest_results', ['id'])
    op.create_index('ix_backtest_results_backtest_id', 'backtest_results', ['backtest_id'])
    
    # Backtest Trades
    op.create_table(
        'backtest_trades',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('backtest_id', sa.String(36), sa.ForeignKey('backtests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('entry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=True),
        sa.Column('pnl_pct', sa.Float(), nullable=True),
        sa.Column('commission', sa.Float(), nullable=False, server_default='0'),
        sa.Column('slippage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.Column('entry_signal', sa.String(50), nullable=True),
        sa.Column('exit_signal', sa.String(50), nullable=True),
        sa.Column('indicators_at_entry', sa.JSON(), nullable=True),
        sa.Column('is_open', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_backtest_trades_id', 'backtest_trades', ['id'])
    op.create_index('ix_backtest_trades_backtest_id', 'backtest_trades', ['backtest_id'])
    op.create_index('ix_backtest_trades_symbol', 'backtest_trades', ['symbol'])
    op.create_index('ix_backtest_trades_entry_date', 'backtest_trades', ['entry_date'])
    op.create_index('ix_backtest_trades_exit_date', 'backtest_trades', ['exit_date'])
    
    # =========================================================================
    # Portfolio Analytics Tables
    # =========================================================================
    
    # Portfolio Snapshots
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_equity', sa.Float(), nullable=False),
        sa.Column('cash_balance', sa.Float(), nullable=False),
        sa.Column('positions_value', sa.Float(), nullable=False),
        sa.Column('daily_pnl', sa.Float(), nullable=False, server_default='0'),
        sa.Column('daily_return_pct', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_return_pct', sa.Float(), nullable=False, server_default='0'),
        sa.Column('num_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_long_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_short_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_portfolio_snapshots_user_date', 'portfolio_snapshots', ['user_id', 'snapshot_date'])
    op.create_index('idx_portfolio_snapshots_date', 'portfolio_snapshots', ['snapshot_date'])
    
    # Performance Metrics
    op.create_table(
        'performance_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_return', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_return_pct', sa.Float(), nullable=False, server_default='0'),
        sa.Column('annualized_return', sa.Float(), nullable=True),
        sa.Column('volatility', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('sortino_ratio', sa.Float(), nullable=True),
        sa.Column('calmar_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('max_drawdown_pct', sa.Float(), nullable=True),
        sa.Column('current_drawdown', sa.Float(), nullable=True),
        sa.Column('current_drawdown_pct', sa.Float(), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winning_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losing_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('avg_win', sa.Float(), nullable=True),
        sa.Column('avg_loss', sa.Float(), nullable=True),
        sa.Column('profit_factor', sa.Float(), nullable=True),
        sa.Column('num_trades_long', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_trades_short', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_holding_period_days', sa.Float(), nullable=True),
        sa.Column('benchmark_return', sa.Float(), nullable=True),
        sa.Column('benchmark_return_pct', sa.Float(), nullable=True),
        sa.Column('alpha', sa.Float(), nullable=True),
        sa.Column('beta', sa.Float(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_performance_metrics_user_period', 'performance_metrics', ['user_id', 'period'])
    op.create_index('idx_performance_metrics_period', 'performance_metrics', ['period'])
    op.create_index('idx_performance_metrics_end_date', 'performance_metrics', ['end_date'])
    
    # Tax Lots
    op.create_table(
        'tax_lots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('acquisition_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('acquisition_price', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('disposition_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disposition_price', sa.Float(), nullable=True),
        sa.Column('total_proceeds', sa.Float(), nullable=True),
        sa.Column('realized_gain_loss', sa.Float(), nullable=True),
        sa.Column('holding_period_days', sa.Integer(), nullable=True),
        sa.Column('is_long_term', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('remaining_quantity', sa.Float(), nullable=False),
        sa.Column('acquisition_trade_id', sa.String(36), nullable=True),
        sa.Column('disposition_trade_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('idx_tax_lots_user_symbol', 'tax_lots', ['user_id', 'symbol'])
    op.create_index('idx_tax_lots_symbol', 'tax_lots', ['symbol'])
    op.create_index('idx_tax_lots_status', 'tax_lots', ['status'])
    op.create_index('idx_tax_lots_acquisition_date', 'tax_lots', ['acquisition_date'])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    
    # Portfolio Analytics
    op.drop_table('tax_lots')
    op.drop_table('performance_metrics')
    op.drop_table('portfolio_snapshots')
    
    # Backtesting
    op.drop_table('backtest_trades')
    op.drop_table('backtest_results')
    op.drop_table('backtests')
    
    # Live Trading
    op.drop_table('signal_history')
    op.drop_table('live_strategies')
    
    # Strategy Execution
    op.drop_table('strategy_performance')
    op.drop_table('strategy_signals')
    op.drop_table('strategy_executions')
    
    # API Keys
    op.drop_table('api_key_audit_logs')
    op.drop_table('api_keys')
    
    # Notifications
    op.drop_table('notification_preferences')
    op.drop_table('notifications')
    
    # Risk & Snapshots
    op.drop_table('risk_rules')
    op.drop_table('position_snapshots')
    
    # Orders
    op.drop_table('orders')
    
    # Trading
    op.drop_table('positions')
    op.drop_table('trades')
    
    # Strategies
    op.drop_table('strategy_tickers')
    op.drop_table('strategies')
    
    # Core
    op.drop_table('market_data_cache')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS tradetype')
    op.execute('DROP TYPE IF EXISTS tradestatus')
    op.execute('DROP TYPE IF EXISTS ordersideenum')
    op.execute('DROP TYPE IF EXISTS ordertypeenum')
    op.execute('DROP TYPE IF EXISTS orderstatusenum')
    op.execute('DROP TYPE IF EXISTS riskruletype')
    op.execute('DROP TYPE IF EXISTS riskruleaction')
    op.execute('DROP TYPE IF EXISTS notificationtype')
    op.execute('DROP TYPE IF EXISTS notificationpriority')
    op.execute('DROP TYPE IF EXISTS notificationchannel')
    op.execute('DROP TYPE IF EXISTS brokertype')
    op.execute('DROP TYPE IF EXISTS apikeystatus')
    op.execute('DROP TYPE IF EXISTS executionstate')
    op.execute('DROP TYPE IF EXISTS signaltype')
    op.execute('DROP TYPE IF EXISTS livestrategystatusenum')
    op.execute('DROP TYPE IF EXISTS backteststatus')
