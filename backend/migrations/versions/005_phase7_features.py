"""Phase 7 features: risk management, notifications, API keys

Revision ID: 005_phase7_features
Revises: 004_backtesting
Create Date: 2025-10-20 18:54:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_phase7_features'
down_revision = '004_backtesting'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create risk_rules table
    op.create_table(
        'risk_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('strategy_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.Enum(
            'MAX_POSITION_SIZE', 'MAX_DAILY_LOSS', 'MAX_DRAWDOWN',
            'MAX_CORRELATION', 'MAX_LEVERAGE', 'POSITION_LIMIT',
            'SECTOR_LIMIT', 'STOP_LOSS', 'TAKE_PROFIT',
            name='riskruletype'
        ), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('threshold_unit', sa.String(length=20), nullable=False, server_default='percent'),
        sa.Column('action', sa.Enum(
            'ALERT', 'BLOCK', 'CLOSE_POSITION', 'CLOSE_ALL', 'REDUCE_SIZE',
            name='riskruleaction'
        ), nullable=False, server_default='ALERT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('breach_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_breach_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_rules_id'), 'risk_rules', ['id'], unique=False)
    op.create_index(op.f('ix_risk_rules_user_id'), 'risk_rules', ['user_id'], unique=False)
    op.create_index(op.f('ix_risk_rules_strategy_id'), 'risk_rules', ['strategy_id'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('type', sa.Enum(
            'ORDER_FILLED', 'ORDER_CANCELLED', 'ORDER_REJECTED',
            'POSITION_OPENED', 'POSITION_CLOSED', 'STRATEGY_SIGNAL',
            'RISK_BREACH', 'DAILY_SUMMARY', 'SYSTEM_ALERT',
            'PROFIT_TARGET', 'STOP_LOSS',
            name='notificationtype'
        ), nullable=False),
        sa.Column('priority', sa.Enum(
            'LOW', 'MEDIUM', 'HIGH', 'URGENT',
            name='notificationpriority'
        ), nullable=False, server_default='MEDIUM'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('strategy_id', sa.String(length=36), nullable=True),
        sa.Column('order_id', sa.String(length=36), nullable=True),
        sa.Column('trade_id', sa.String(length=36), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_via', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)

    # Create notification_preferences table
    op.create_table(
        'notification_preferences',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('notification_type', sa.Enum(
            'ORDER_FILLED', 'ORDER_CANCELLED', 'ORDER_REJECTED',
            'POSITION_OPENED', 'POSITION_CLOSED', 'STRATEGY_SIGNAL',
            'RISK_BREACH', 'DAILY_SUMMARY', 'SYSTEM_ALERT',
            'PROFIT_TARGET', 'STOP_LOSS',
            name='notificationtype'
        ), nullable=False),
        sa.Column('channel', sa.Enum(
            'EMAIL', 'IN_APP', 'PUSH', 'SMS', 'WEBHOOK',
            name='notificationchannel'
        ), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('min_priority', sa.Enum(
            'LOW', 'MEDIUM', 'HIGH', 'URGENT',
            name='notificationpriority'
        ), nullable=False, server_default='LOW'),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('quiet_start_hour', sa.Integer(), nullable=True),
        sa.Column('quiet_end_hour', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('webhook_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('broker', sa.Enum(
            'ALPACA', 'INTERACTIVE_BROKERS', 'TD_AMERITRADE',
            'ROBINHOOD', 'COINBASE', 'BINANCE',
            name='brokertype'
        ), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('encrypted_api_secret', sa.Text(), nullable=False),
        sa.Column('encryption_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('account_id', sa.String(length=255), nullable=True),
        sa.Column('base_url', sa.String(length=512), nullable=True),
        sa.Column('is_paper_trading', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('status', sa.Enum(
            'ACTIVE', 'INACTIVE', 'EXPIRED', 'REVOKED',
            name='apikeystatus'
        ), nullable=False, server_default='ACTIVE'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rotation_history', sa.Text(), nullable=True),
        sa.Column('last_rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_keys_broker'), 'api_keys', ['broker'], unique=False)

    # Create api_key_audit_logs table
    op.create_table(
        'api_key_audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('api_key_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_key_audit_logs_id'), 'api_key_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_api_key_audit_logs_api_key_id'), 'api_key_audit_logs', ['api_key_id'], unique=False)
    op.create_index(op.f('ix_api_key_audit_logs_user_id'), 'api_key_audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_key_audit_logs_action'), 'api_key_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_api_key_audit_logs_created_at'), 'api_key_audit_logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_api_key_audit_logs_created_at'), table_name='api_key_audit_logs')
    op.drop_index(op.f('ix_api_key_audit_logs_action'), table_name='api_key_audit_logs')
    op.drop_index(op.f('ix_api_key_audit_logs_user_id'), table_name='api_key_audit_logs')
    op.drop_index(op.f('ix_api_key_audit_logs_api_key_id'), table_name='api_key_audit_logs')
    op.drop_index(op.f('ix_api_key_audit_logs_id'), table_name='api_key_audit_logs')
    op.drop_table('api_key_audit_logs')
    
    op.drop_index(op.f('ix_api_keys_broker'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
    
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    op.drop_index(op.f('ix_risk_rules_strategy_id'), table_name='risk_rules')
    op.drop_index(op.f('ix_risk_rules_user_id'), table_name='risk_rules')
    op.drop_index(op.f('ix_risk_rules_id'), table_name='risk_rules')
    op.drop_table('risk_rules')
    
    # Drop enum types
    sa.Enum(name='apikeystatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='brokertype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='notificationchannel').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='notificationpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='notificationtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='riskruleaction').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='riskruletype').drop(op.get_bind(), checkfirst=True)
