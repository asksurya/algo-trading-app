"""
Add live trading automation tables

Revision ID: 007
Revises: 006
Create Date: 2025-10-25 11:57:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    """Create live_strategies and signal_history tables for automated trading."""
    
    # Create live_strategies table
    op.create_table(
        'live_strategies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('symbols', sa.JSON(), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'PAUSED', 'STOPPED', 'ERROR', name='livestrategyenum'), nullable=False, server_default='STOPPED'),
        sa.Column('check_interval', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('auto_execute', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('max_position_size', sa.Float(), nullable=True),
        sa.Column('max_positions', sa.Integer(), nullable=True, server_default='5'),
        sa.Column('daily_loss_limit', sa.Float(), nullable=True),
        sa.Column('position_size_pct', sa.Float(), nullable=True, server_default='0.02'),
        sa.Column('last_check', sa.DateTime(), nullable=True),
        sa.Column('last_signal', sa.DateTime(), nullable=True),
        sa.Column('state', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('total_signals', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('executed_trades', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_positions', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('daily_pnl', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('total_pnl', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ondelete='CASCADE')
    )
    
    # Create indexes for live_strategies
    op.create_index('idx_live_strategies_user_id', 'live_strategies', ['user_id'])
    op.create_index('idx_live_strategies_status', 'live_strategies', ['status'])
    op.create_index('idx_live_strategies_strategy_id', 'live_strategies', ['strategy_id'])
    
    # Create signal_history table
    op.create_table(
        'signal_history',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('live_strategy_id', sa.String(length=36), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('signal_type', sa.Enum('BUY', 'SELL', 'HOLD', name='signaltypeenum'), nullable=False),
        sa.Column('signal_strength', sa.Float(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('indicators', sa.JSON(), nullable=True),
        sa.Column('executed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('execution_price', sa.Float(), nullable=True),
        sa.Column('order_id', sa.String(length=36), nullable=True),
        sa.Column('execution_time', sa.DateTime(), nullable=True),
        sa.Column('execution_error', sa.String(length=500), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['live_strategy_id'], ['live_strategies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL')
    )
    
    # Create indexes for signal_history
    op.create_index('idx_signal_history_live_strategy_id', 'signal_history', ['live_strategy_id'])
    op.create_index('idx_signal_history_symbol', 'signal_history', ['symbol'])
    op.create_index('idx_signal_history_timestamp', 'signal_history', ['timestamp'])
    op.create_index('idx_signal_history_executed', 'signal_history', ['executed'])


def downgrade():
    """Drop live trading tables."""
    # Drop signal_history table and its indexes
    op.drop_index('idx_signal_history_executed', table_name='signal_history')
    op.drop_index('idx_signal_history_timestamp', table_name='signal_history')
    op.drop_index('idx_signal_history_symbol', table_name='signal_history')
    op.drop_index('idx_signal_history_live_strategy_id', table_name='signal_history')
    op.drop_table('signal_history')
    
    # Drop live_strategies table and its indexes
    op.drop_index('idx_live_strategies_strategy_id', table_name='live_strategies')
    op.drop_index('idx_live_strategies_status', table_name='live_strategies')
    op.drop_index('idx_live_strategies_user_id', table_name='live_strategies')
    op.drop_table('live_strategies')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS signaltypeenum')
    op.execute('DROP TYPE IF EXISTS livestrategyenum')
