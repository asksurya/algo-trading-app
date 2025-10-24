"""Add strategy execution tracking tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create strategy execution tracking tables."""
    
    # Create signal type enum
    op.execute("CREATE TYPE signaltype AS ENUM ('buy', 'sell', 'hold')")
    
    # Create execution state enum
    op.execute("CREATE TYPE executionstate AS ENUM ('active', 'inactive', 'paused', 'error', 'circuit_breaker')")
    
    # Create strategy_executions table
    op.create_table(
        'strategy_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('state', sa.Enum('active', 'inactive', 'paused', 'error', 'circuit_breaker', name='executionstate'), nullable=False),
        sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_signal_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_trade_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trades_today', sa.Integer(), nullable=False, default=0),
        sa.Column('max_trades_per_day', sa.Integer(), nullable=False, default=10),
        sa.Column('loss_today', sa.Float(), nullable=False, default=0.0),
        sa.Column('max_loss_per_day', sa.Float(), nullable=False, default=1000.0),
        sa.Column('consecutive_losses', sa.Integer(), nullable=False, default=0),
        sa.Column('max_consecutive_losses', sa.Integer(), nullable=False, default=3),
        sa.Column('circuit_breaker_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('has_open_position', sa.Boolean(), nullable=False, default=False),
        sa.Column('current_position_qty', sa.Float(), nullable=True),
        sa.Column('current_position_entry_price', sa.Float(), nullable=True),
        sa.Column('config_overrides', sa.JSON(), nullable=True),
        sa.Column('is_dry_run', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes for strategy_executions table
    op.create_index('idx_strategy_executions_id', 'strategy_executions', ['id'])
    op.create_index('idx_strategy_executions_strategy_id', 'strategy_executions', ['strategy_id'])
    op.create_index('idx_strategy_executions_state', 'strategy_executions', ['state'])
    
    # Create strategy_signals table
    op.create_table(
        'strategy_signals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('execution_id', sa.String(36), sa.ForeignKey('strategy_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('signal_type', sa.Enum('buy', 'sell', 'hold', name='signaltype'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('signal_strength', sa.Float(), nullable=True),
        sa.Column('price_at_signal', sa.Float(), nullable=False),
        sa.Column('indicator_values', sa.JSON(), nullable=False, default=dict),
        sa.Column('reasoning', sa.Text(), nullable=False),
        sa.Column('was_executed', sa.Boolean(), nullable=False, default=False),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True),
        sa.Column('execution_error', sa.Text(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for strategy_signals table
    op.create_index('idx_strategy_signals_id', 'strategy_signals', ['id'])
    op.create_index('idx_strategy_signals_strategy_id', 'strategy_signals', ['strategy_id'])
    op.create_index('idx_strategy_signals_execution_id', 'strategy_signals', ['execution_id'])
    op.create_index('idx_strategy_signals_signal_type', 'strategy_signals', ['signal_type'])
    op.create_index('idx_strategy_signals_symbol', 'strategy_signals', ['symbol'])
    op.create_index('idx_strategy_signals_generated_at', 'strategy_signals', ['generated_at'])
    op.create_index('idx_strategy_signals_strategy_generated', 'strategy_signals', ['strategy_id', 'generated_at'])
    
    # Create strategy_performance table
    op.create_table(
        'strategy_performance',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False, default='daily'),
        sa.Column('total_trades', sa.Integer(), nullable=False, default=0),
        sa.Column('winning_trades', sa.Integer(), nullable=False, default=0),
        sa.Column('losing_trades', sa.Integer(), nullable=False, default=0),
        sa.Column('total_pnl', sa.Float(), nullable=False, default=0.0),
        sa.Column('gross_profit', sa.Float(), nullable=False, default=0.0),
        sa.Column('gross_loss', sa.Float(), nullable=False, default=0.0),
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
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes for strategy_performance table
    op.create_index('idx_strategy_performance_id', 'strategy_performance', ['id'])
    op.create_index('idx_strategy_performance_strategy_id', 'strategy_performance', ['strategy_id'])
    op.create_index('idx_strategy_performance_date', 'strategy_performance', ['date'])
    op.create_index('idx_strategy_performance_strategy_date', 'strategy_performance', ['strategy_id', 'date'])
    op.create_index('idx_strategy_performance_period_type', 'strategy_performance', ['period_type'])


def downgrade() -> None:
    """Drop strategy execution tracking tables."""
    
    # Drop strategy_performance table and indexes
    op.drop_index('idx_strategy_performance_period_type', 'strategy_performance')
    op.drop_index('idx_strategy_performance_strategy_date', 'strategy_performance')
    op.drop_index('idx_strategy_performance_date', 'strategy_performance')
    op.drop_index('idx_strategy_performance_strategy_id', 'strategy_performance')
    op.drop_index('idx_strategy_performance_id', 'strategy_performance')
    op.drop_table('strategy_performance')
    
    # Drop strategy_signals table and indexes
    op.drop_index('idx_strategy_signals_strategy_generated', 'strategy_signals')
    op.drop_index('idx_strategy_signals_generated_at', 'strategy_signals')
    op.drop_index('idx_strategy_signals_symbol', 'strategy_signals')
    op.drop_index('idx_strategy_signals_signal_type', 'strategy_signals')
    op.drop_index('idx_strategy_signals_execution_id', 'strategy_signals')
    op.drop_index('idx_strategy_signals_strategy_id', 'strategy_signals')
    op.drop_index('idx_strategy_signals_id', 'strategy_signals')
    op.drop_table('strategy_signals')
    
    # Drop strategy_executions table and indexes
    op.drop_index('idx_strategy_executions_state', 'strategy_executions')
    op.drop_index('idx_strategy_executions_strategy_id', 'strategy_executions')
    op.drop_index('idx_strategy_executions_id', 'strategy_executions')
    op.drop_table('strategy_executions')
    
    # Drop enums
    op.execute('DROP TYPE executionstate')
    op.execute('DROP TYPE signaltype')