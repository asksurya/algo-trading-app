"""Add backtesting tables

Revision ID: 004
Revises: 003
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create backtesting tables."""
    
    # Create backtest status enum
    op.execute("CREATE TYPE backteststatus AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled')")
    
    # Create backtests table
    op.create_table(
        'backtests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('strategy_id', sa.String(36), sa.ForeignKey('strategies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('initial_capital', sa.Float, nullable=False, server_default='100000.0'),
        sa.Column('commission', sa.Float, nullable=False, server_default='0.001'),
        sa.Column('slippage', sa.Float, nullable=False, server_default='0.0005'),
        sa.Column('strategy_params', postgresql.JSON, nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', name='backteststatus'), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer, nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('total_trades', sa.Integer, nullable=True),
        sa.Column('winning_trades', sa.Integer, nullable=True),
        sa.Column('losing_trades', sa.Integer, nullable=True),
        sa.Column('total_return', sa.Float, nullable=True),
        sa.Column('total_pnl', sa.Float, nullable=True),
        sa.Column('max_drawdown', sa.Float, nullable=True),
        sa.Column('sharpe_ratio', sa.Float, nullable=True),
        sa.Column('win_rate', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for backtests
    op.create_index('ix_backtests_id', 'backtests', ['id'])
    op.create_index('ix_backtests_user_id', 'backtests', ['user_id'])
    op.create_index('ix_backtests_strategy_id', 'backtests', ['strategy_id'])
    op.create_index('ix_backtests_status', 'backtests', ['status'])
    op.create_index('ix_backtests_start_date', 'backtests', ['start_date'])
    op.create_index('ix_backtests_end_date', 'backtests', ['end_date'])
    
    # Create backtest_results table
    op.create_table(
        'backtest_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('backtest_id', sa.String(36), sa.ForeignKey('backtests.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('final_capital', sa.Float, nullable=False),
        sa.Column('total_return_pct', sa.Float, nullable=False),
        sa.Column('annualized_return', sa.Float, nullable=False),
        sa.Column('total_trades', sa.Integer, nullable=False, server_default='0'),
        sa.Column('winning_trades', sa.Integer, nullable=False, server_default='0'),
        sa.Column('losing_trades', sa.Integer, nullable=False, server_default='0'),
        sa.Column('win_rate', sa.Float, nullable=False),
        sa.Column('gross_profit', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('gross_loss', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('net_profit', sa.Float, nullable=False),
        sa.Column('profit_factor', sa.Float, nullable=True),
        sa.Column('avg_trade_pnl', sa.Float, nullable=False),
        sa.Column('avg_winning_trade', sa.Float, nullable=True),
        sa.Column('avg_losing_trade', sa.Float, nullable=True),
        sa.Column('largest_win', sa.Float, nullable=True),
        sa.Column('largest_loss', sa.Float, nullable=True),
        sa.Column('max_drawdown_pct', sa.Float, nullable=False),
        sa.Column('max_drawdown_dollars', sa.Float, nullable=False),
        sa.Column('sharpe_ratio', sa.Float, nullable=True),
        sa.Column('sortino_ratio', sa.Float, nullable=True),
        sa.Column('calmar_ratio', sa.Float, nullable=True),
        sa.Column('volatility', sa.Float, nullable=True),
        sa.Column('avg_trade_duration_hours', sa.Float, nullable=True),
        sa.Column('market_exposure_pct', sa.Float, nullable=True),
        sa.Column('equity_curve', postgresql.JSON, nullable=False, server_default='{}'),
        sa.Column('drawdown_periods', postgresql.JSON, nullable=True),
        sa.Column('monthly_returns', postgresql.JSON, nullable=True),
        sa.Column('additional_metrics', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create indexes for backtest_results
    op.create_index('ix_backtest_results_id', 'backtest_results', ['id'])
    op.create_index('ix_backtest_results_backtest_id', 'backtest_results', ['backtest_id'])
    
    # Create backtest_trades table
    op.create_table(
        'backtest_trades',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('backtest_id', sa.String(36), sa.ForeignKey('backtests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('side', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('entry_price', sa.Float, nullable=False),
        sa.Column('exit_price', sa.Float, nullable=True),
        sa.Column('entry_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exit_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pnl', sa.Float, nullable=True),
        sa.Column('pnl_pct', sa.Float, nullable=True),
        sa.Column('commission', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('slippage', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('duration_hours', sa.Float, nullable=True),
        sa.Column('entry_signal', sa.String(50), nullable=True),
        sa.Column('exit_signal', sa.String(50), nullable=True),
        sa.Column('indicators_at_entry', postgresql.JSON, nullable=True),
        sa.Column('is_open', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Create indexes for backtest_trades
    op.create_index('ix_backtest_trades_id', 'backtest_trades', ['id'])
    op.create_index('ix_backtest_trades_backtest_id', 'backtest_trades', ['backtest_id'])
    op.create_index('ix_backtest_trades_symbol', 'backtest_trades', ['symbol'])
    op.create_index('ix_backtest_trades_entry_date', 'backtest_trades', ['entry_date'])
    op.create_index('ix_backtest_trades_exit_date', 'backtest_trades', ['exit_date'])


def downgrade() -> None:
    """Drop backtesting tables."""
    
    # Drop tables
    op.drop_table('backtest_trades')
    op.drop_table('backtest_results')
    op.drop_table('backtests')
    
    # Drop enum type
    op.execute("DROP TYPE backteststatus")
