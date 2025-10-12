"""
Base Strategy Class

All trading strategies should inherit from this base class.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from enum import Enum


class Signal(Enum):
    """Trading signals."""
    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, name: str):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
        """
        self.name = name
        self.positions = {}  # Current positions {symbol: shares}
        self.signals = []  # Historical signals
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on market data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Series with signals (1=BUY, -1=SELL, 0=HOLD)
        """
        pass
    
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators needed for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added indicator columns
        """
        pass
    
    def get_position_size(
        self,
        symbol: str,
        signal: Signal,
        current_price: float,
        portfolio_value: float,
        max_position_size: float = 0.1
    ) -> int:
        """
        Calculate position size for a trade.
        
        Args:
            symbol: Stock symbol
            signal: Trading signal
            current_price: Current stock price
            portfolio_value: Total portfolio value
            max_position_size: Max % of portfolio per position
            
        Returns:
            Number of shares to trade
        """
        if signal == Signal.HOLD:
            return 0
        
        # Calculate max investment amount
        max_investment = portfolio_value * max_position_size
        
        # Calculate shares (rounded down)
        shares = int(max_investment / current_price)
        
        if signal == Signal.BUY:
            return shares
        elif signal == Signal.SELL:
            # Sell all shares if we have a position
            return -self.positions.get(symbol, 0)
        
        return 0
    
    def update_position(self, symbol: str, shares: int):
        """
        Update position after a trade.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares (positive for buy, negative for sell)
        """
        current_position = self.positions.get(symbol, 0)
        new_position = current_position + shares
        
        if new_position == 0:
            # Close position
            if symbol in self.positions:
                del self.positions[symbol]
        else:
            self.positions[symbol] = new_position
    
    def get_current_position(self, symbol: str) -> int:
        """Get current position for a symbol."""
        return self.positions.get(symbol, 0)
    
    def has_position(self, symbol: str) -> bool:
        """Check if we have a position in a symbol."""
        return symbol in self.positions and self.positions[symbol] != 0
    
    def reset(self):
        """Reset strategy state."""
        self.positions = {}
        self.signals = []
    
    def __str__(self) -> str:
        return f"{self.name} Strategy"
    
    def __repr__(self) -> str:
        return self.__str__()


class StrategyMetrics:
    """Calculate performance metrics for a strategy."""
    
    @staticmethod
    def calculate_returns(equity_curve: pd.Series) -> float:
        """Calculate total returns."""
        return (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
    
    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe ratio
        """
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        return sharpe
    
    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """
        Calculate maximum drawdown.
        
        Args:
            equity_curve: Series of portfolio values
            
        Returns:
            Maximum drawdown (as positive decimal)
        """
        cumulative_max = equity_curve.expanding().max()
        drawdown = (equity_curve - cumulative_max) / cumulative_max
        return abs(drawdown.min())
    
    @staticmethod
    def calculate_win_rate(trades: List[Dict]) -> float:
        """
        Calculate win rate from list of trades.
        
        Args:
            trades: List of trade dictionaries with 'profit' key
            
        Returns:
            Win rate (0-1)
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for trade in trades if trade.get('profit', 0) > 0)
        return winning_trades / len(trades)
    
    @staticmethod
    def calculate_profit_factor(trades: List[Dict]) -> float:
        """
        Calculate profit factor.
        
        Args:
            trades: List of trade dictionaries with 'profit' key
            
        Returns:
            Profit factor
        """
        gross_profit = sum(trade['profit'] for trade in trades if trade.get('profit', 0) > 0)
        gross_loss = abs(sum(trade['profit'] for trade in trades if trade.get('profit', 0) < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
