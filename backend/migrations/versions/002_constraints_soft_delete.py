"""Add constraints and soft delete columns

Revision ID: 002_constraints_soft_delete
Revises: consolidated_001
Create Date: 2024-12-10

This migration adds:
1. Unique constraints on NotificationPreference and StrategyTicker
2. Soft delete columns (is_deleted, deleted_at) on Order, Trade, and Backtest tables
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_constraints_soft_delete'
down_revision = 'consolidated_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add unique constraints
    op.create_unique_constraint(
        'uq_user_notification_channel',
        'notification_preferences',
        ['user_id', 'notification_type', 'channel']
    )
    
    op.create_unique_constraint(
        'uq_strategy_ticker',
        'strategy_tickers',
        ['strategy_id', 'ticker']
    )
    
    # Add soft delete columns to orders table
    op.add_column('orders', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('orders', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_orders_is_deleted', 'orders', ['is_deleted'])
    
    # Add soft delete columns to trades table
    op.add_column('trades', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('trades', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_trades_is_deleted', 'trades', ['is_deleted'])
    
    # Add soft delete columns to backtests table
    op.add_column('backtests', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('backtests', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_backtests_is_deleted', 'backtests', ['is_deleted'])


def downgrade() -> None:
    # Remove soft delete columns from backtests
    op.drop_index('ix_backtests_is_deleted', table_name='backtests')
    op.drop_column('backtests', 'deleted_at')
    op.drop_column('backtests', 'is_deleted')
    
    # Remove soft delete columns from trades
    op.drop_index('ix_trades_is_deleted', table_name='trades')
    op.drop_column('trades', 'deleted_at')
    op.drop_column('trades', 'is_deleted')
    
    # Remove soft delete columns from orders
    op.drop_index('ix_orders_is_deleted', table_name='orders')
    op.drop_column('orders', 'deleted_at')
    op.drop_column('orders', 'is_deleted')
    
    # Remove unique constraints
    op.drop_constraint('uq_strategy_ticker', 'strategy_tickers', type_='unique')
    op.drop_constraint('uq_user_notification_channel', 'notification_preferences', type_='unique')
