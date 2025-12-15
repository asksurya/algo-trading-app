"""Add paper trading models

Revision ID: 003_paper_trading
Revises: 002_constraints_soft_delete
Create Date: 2025-02-15 05:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_paper_trading'
down_revision = '002_constraints_soft_delete'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create paper_accounts table
    op.create_table(
        'paper_accounts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('cash_balance', sa.Float(), nullable=False),
        sa.Column('initial_balance', sa.Float(), nullable=False),
        sa.Column('total_pnl', sa.Float(), nullable=True),
        sa.Column('total_return_pct', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_paper_accounts_user_id'), 'paper_accounts', ['user_id'], unique=True)

    # Create paper_positions table
    op.create_table(
        'paper_positions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('avg_price', sa.Float(), nullable=False),
        sa.Column('market_value', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['paper_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_paper_positions_account_id'), 'paper_positions', ['account_id'], unique=False)
    op.create_index(op.f('ix_paper_positions_symbol'), 'paper_positions', ['symbol'], unique=False)

    # Create paper_trades table
    op.create_table(
        'paper_trades',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('account_id', sa.String(length=36), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['paper_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_paper_trades_account_id'), 'paper_trades', ['account_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_paper_trades_account_id'), table_name='paper_trades')
    op.drop_table('paper_trades')
    op.drop_index(op.f('ix_paper_positions_symbol'), table_name='paper_positions')
    op.drop_index(op.f('ix_paper_positions_account_id'), table_name='paper_positions')
    op.drop_table('paper_positions')
    op.drop_index(op.f('ix_paper_accounts_user_id'), table_name='paper_accounts')
    op.drop_table('paper_accounts')
