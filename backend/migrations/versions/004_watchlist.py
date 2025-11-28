"""
Database migration for watchlist and price alerts.

Revision ID: 004_watchlist
Revises: 003_portfolio_analytics
Create Date: 2025-11-27

"""
from alembic import op
import sqlalchemy as sa

#  revision identifiers
revision = '004_watchlist'
down_revision = '003_portfolio_analytics'
branch_labels = None
depends_on = None


def upgrade():
    # Create watchlists table
    op.create_table(
        'watchlists',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    op.create_index('idx_watchlists_user_id', 'watchlists', ['user_id'])
    
    # Create watchlist_items table
    op.create_table(
        'watchlist_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('watchlist_id', sa.String(36), sa.ForeignKey('watchlists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_watchlist_items_watchlist_id', 'watchlist_items', ['watchlist_id'])
    op.create_index('idx_watchlist_items_symbol', 'watchlist_items', ['symbol'])
    
    # Create price_alerts table
    op.create_table(
        'price_alerts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('condition', sa.String(10), nullable=False),  # 'above' or 'below'
        sa.Column('target_price', sa.Float(), nullable=False),
        sa.Column('message', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('idx_price_alerts_user_id', 'price_alerts', ['user_id'])
    op.create_index('idx_price_alerts_symbol', 'price_alerts', ['symbol'])
    op.create_index('idx_price_alerts_is_active', 'price_alerts', ['is_active'])


def downgrade():
    # Drop tables and indexes
    op.drop_index('idx_price_alerts_is_active', table_name='price_alerts')
    op.drop_index('idx_price_alerts_symbol', table_name='price_alerts')
    op.drop_index('idx_price_alerts_user_id', table_name='price_alerts')
    op.drop_table('price_alerts')
    
    op.drop_index('idx_watchlist_items_symbol', table_name='watchlist_items')
    op.drop_index('idx_watchlist_items_watchlist_id', table_name='watchlist_items')
    op.drop_table('watchlist_items')
    
    op.drop_index('idx_watchlists_user_id', table_name='watchlists')
    op.drop_table('watchlists')
