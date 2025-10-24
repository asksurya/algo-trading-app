"""
Pydantic schemas package.
"""
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload,
    PasswordChange,
)
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyTickerCreate,
    StrategyTickerResponse,
    BacktestRequest,
    BacktestResponse,
)
from app.schemas.trade import (
    TradeCreate,
    TradeUpdate,
    TradeResponse,
    PositionResponse,
    TradingStatistics,
    PortfolioSummary,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    "PasswordChange",
    # Strategy
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyResponse",
    "StrategyTickerCreate",
    "StrategyTickerResponse",
    "BacktestRequest",
    "BacktestResponse",
    # Trade
    "TradeCreate",
    "TradeUpdate",
    "TradeResponse",
    "PositionResponse",
    "TradingStatistics",
    "PortfolioSummary",
]
