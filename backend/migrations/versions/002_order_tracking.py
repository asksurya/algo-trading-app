"""Add order and position snapshot tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create orders and position_snapshots tables."""
    
    # Create order side enum
    op.execute("CREATE TYPE ordersideenum AS ENUM ('buy', 'sell')")
    
    # Create order type enum
    op.execute("CREATE TYPE ordertypeenum AS ENUM ('market', 'limit', 'stop', 'stop_limit', 'trailing_stop')")
    
    # Create order status enum
    op.execute("""
        CREATE TYPE orderstatusenum AS ENUM (
            'new', 'partially_filled', 'filled', 'done_for_day', 
            'canceled', 'expired', 'replaced', 'pending_cancel', 
            'pending_replace', 'accepted', 'pending_new', 
            'rejected', 'suspended', 'stopped'
        )
    """)
    
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('alpaca_order_id', sa.String(), unique=True, nullable=False),
        sa.Column('client_order_id', sa.String(), nullable=True),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('side', sa.Enum('buy', 'sell', name='ordersideenum'), nullable=False),
        sa.Column('order_type', sa.Enum('market', 'limit', 'stop', 'stop_limit', 'trailing_stop', name='ordertypeenum'), nullable=False),
        sa.Column('time_in_force', sa.String(10), nullable=False),
        sa.Column('qty', sa.Float(), nullable=True),
        sa.Column('notional', sa.Float(), nullable=True),
        sa.Column('filled_qty', sa.Float(), default=0.0, nullable=False),
        sa.Column('limit_price', sa.Float(), nullable=True),
        sa.Column('stop_price', sa.Float(), nullable=True),
        sa.Column('filled_avg_price', sa.Float(), nullable=True),
        sa.Column('trail_price', sa.Float(), nullable=True),
        sa.Column('trail_percent', sa.Float(), nullable=True),
        sa.Column('hwm', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum(
            'new', 'partially_filled', 'filled', 'done_for_day', 
            'canceled', 'expired', 'replaced', 'pending_cancel', 
            'pending_replace', 'accepted', 'pending_new', 
            'rejected', 'suspended', 'stopped',
            name='orderstatusenum'
        ), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('expired_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_at', sa.DateTime(), nullable=True),
        sa.Column('replaced_by', sa.String(), nullable=True),
        sa.Column('replaces', sa.String(), nullable=True),
        sa.Column('extended_hours', sa.Boolean(), default=False, nullable=False),
        sa.Column('asset_class', sa.String(20), default='us_equity', nullable=False),
        sa.Column('asset_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for orders table
    op.create_index('idx_orders_alpaca_order_id', 'orders', ['alpaca_order_id'])
    op.create_index('idx_orders_symbol', 'orders', ['symbol'])
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_user_created', 'orders', ['user_id', 'created_at'])
    op.create_index('idx_orders_symbol_created', 'orders', ['symbol', 'created_at'])
    op.create_index('idx_orders_status_created', 'orders', ['status', 'created_at'])
    op.create_index('idx_orders_user_symbol', 'orders', ['user_id', 'symbol'])
    
    # Create position_snapshots table
    op.create_table(
        'position_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('side', sa.Enum('buy', 'sell', name='ordersideenum'), nullable=False),
        sa.Column('avg_entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('market_value', sa.Float(), nullable=False),
        sa.Column('cost_basis', sa.Float(), nullable=False),
        sa.Column('unrealized_pl', sa.Float(), nullable=False),
        sa.Column('unrealized_plpc', sa.Float(), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for position_snapshots table
    op.create_index('idx_position_snapshots_symbol', 'position_snapshots', ['symbol'])
    op.create_index('idx_position_snapshots_snapshot_at', 'position_snapshots', ['snapshot_at'])
    op.create_index('idx_position_snapshots_user_time', 'position_snapshots', ['user_id', 'snapshot_at'])
    op.create_index('idx_position_snapshots_symbol_time', 'position_snapshots', ['symbol', 'snapshot_at'])


def downgrade() -> None:
    """Drop orders and position_snapshots tables."""
    
    # Drop position_snapshots table and indexes
    op.drop_index('idx_position_snapshots_symbol_time', 'position_snapshots')
    op.drop_index('idx_position_snapshots_user_time', 'position_snapshots')
    op.drop_index('idx_position_snapshots_snapshot_at', 'position_snapshots')
    op.drop_index('idx_position_snapshots_symbol', 'position_snapshots')
    op.drop_table('position_snapshots')
    
    # Drop orders table and indexes
    op.drop_index('idx_orders_user_symbol', 'orders')
    op.drop_index('idx_orders_status_created', 'orders')
    op.drop_index('idx_orders_symbol_created', 'orders')
    op.drop_index('idx_orders_user_created', 'orders')
    op.drop_index('idx_orders_status', 'orders')
    op.drop_index('idx_orders_symbol', 'orders')
    op.drop_index('idx_orders_alpaca_order_id', 'orders')
    op.drop_table('orders')
    
    # Drop enums
    op.execute('DROP TYPE orderstatusenum')
    op.execute('DROP TYPE ordertypeenum')
    op.execute('DROP TYPE ordersideenum')