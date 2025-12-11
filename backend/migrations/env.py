"""
Alembic migration environment configuration.

This module configures the Alembic migration environment to work with
the async SQLAlchemy 2.0 engine and imports all models for autogenerate support.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.models.base import Base

# Import ALL models to ensure they are registered with Base.metadata
# This is critical for Alembic autogenerate to work properly
from app.models import (
    # User
    User,
    # Strategy
    Strategy,
    StrategyTicker,
    # Trading
    Trade,
    Position,
    Order,
    PositionSnapshot,
    # Risk
    RiskRule,
    # Notification
    Notification,
    NotificationPreference,
    # API Keys
    ApiKey,
    ApiKeyAuditLog,
    # Market Data
    MarketDataCache,
    # Live Trading
    LiveStrategy,
    SignalHistory,
    # Backtesting
    Backtest,
    BacktestResult,
    BacktestTrade,
    # Strategy Execution
    StrategyExecution,
    StrategySignal,
    StrategyPerformance,
    # Portfolio Analytics
    PortfolioSnapshot,
    PerformanceMetrics,
    TaxLot,
)

# Alembic Config object
config = context.config

# Get database URL from settings, handling async->sync conversion
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
elif database_url.startswith("sqlite+aiosqlite://"):
    database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
# Skip logging config if not present in alembic.ini
try:
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)
except KeyError:
    # No logging configuration in alembic.ini, skip it
    pass

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
