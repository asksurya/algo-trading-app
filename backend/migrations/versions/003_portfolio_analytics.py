"""
Database migration for portfolio analytics tables.

Revision ID: 003_portfolio_analytics
Revises: 002_order_tracking
Create Date: 2025-11-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_portfolio_analytics'
down_revision = '002_order_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Create portfolio_snapshots table
    op.create_table(
        'portfolio_snapshots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.Column('total_equity', sa.Float(), nullable=False),
        sa.Column('cash_balance', sa.Float(), nullable=False),
        sa.Column('positions_value', sa.Float(), nullable=False),
        sa.Column('daily_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('daily_return_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_return_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('num_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_long_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_short_positions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_portfolio_snapshots_user_date', 'portfolio_snapshots', ['user_id', 'snapshot_date'])
    op.create_index('idx_portfolio_snapshots_date', 'portfolio_snapshots', ['snapshot_date'])
    
    # Create performance_metrics table
    op.create_table(
        'performance_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('total_return', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_return_pct', sa.Float(), nullable=False, server_default='0.0'),
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
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_performance_metrics_user_period', 'performance_metrics', ['user_id', 'period'])
    op.create_index('idx_performance_metrics_period', 'performance_metrics', ['period'])
    op.create_index('idx_performance_metrics_end_date', 'performance_metrics', ['end_date'])
    
    # Create tax_lots table
    op.create_table(
        'tax_lots',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('acquisition_date', sa.DateTime(), nullable=False),
        sa.Column('acquisition_price', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('disposition_date', sa.DateTime(), nullable=True),
        sa.Column('disposition_price', sa.Float(), nullable=True),
        sa.Column('total_proceeds', sa.Float(), nullable=True),
        sa.Column('realized_gain_loss', sa.Float(), nullable=True),
        sa.Column('holding_period_days', sa.Integer(), nullable=True),
        sa.Column('is_long_term', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('remaining_quantity', sa.Float(), nullable=False),
        sa.Column('acquisition_trade_id', sa.String(36), nullable=True),
        sa.Column('disposition_trade_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('idx_tax_lots_user_symbol', 'tax_lots', ['user_id', 'symbol'])
    op.create_index('idx_tax_lots_symbol', 'tax_lots', ['symbol'])
    op.create_index('idx_tax_lots_status', 'tax_lots', ['status'])
    op.create_index('idx_tax_lots_acquisition_date', 'tax_lots', ['acquisition_date'])


def downgrade():
    # Drop tables and indexes
    op.drop_index('idx_tax_lots_acquisition_date', table_name='tax_lots')
    op.drop_index('idx_tax_lots_status', table_name='tax_lots')
    op.drop_index('idx_tax_lots_symbol', table_name='tax_lots')
    op.drop_index('idx_tax_lots_user_symbol', table_name='tax_lots')
    op.drop_table('tax_lots')
    
    op.drop_index('idx_performance_metrics_end_date', table_name='performance_metrics')
    op.drop_index('idx_performance_metrics_period', table_name='performance_metrics')
    op.drop_index('idx_performance_metrics_user_period', table_name='performance_metrics')
    op.drop_table('performance_metrics')
    
    op.drop_index('idx_portfolio_snapshots_date', table_name='portfolio_snapshots')
    op.drop_index('idx_portfolio_snapshots_user_date', table_name='portfolio_snapshots')
    op.drop_table('portfolio_snapshots')
