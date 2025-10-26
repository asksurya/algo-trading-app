"""
Add market data cache table

Revision ID: 006
Revises: 005
Create Date: 2025-10-24 22:17:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '006'
down_revision = '005_phase7_features'
branch_labels = None
depends_on = None


def upgrade():
    """Create market_data_cache table for storing historical price data."""
    op.create_table(
        'market_data_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), server_default='alpaca'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'date', name='uix_symbol_date')
    )
    
    # Create indexes for fast lookups
    op.create_index('idx_market_data_cache_symbol', 'market_data_cache', ['symbol'])
    op.create_index('idx_market_data_cache_date', 'market_data_cache', ['date'])
    op.create_index('idx_symbol_date_range', 'market_data_cache', ['symbol', 'date'])


def downgrade():
    """Drop market_data_cache table."""
    op.drop_index('idx_symbol_date_range', table_name='market_data_cache')
    op.drop_index('idx_market_data_cache_date', table_name='market_data_cache')
    op.drop_index('idx_market_data_cache_symbol', table_name='market_data_cache')
    op.drop_table('market_data_cache')
