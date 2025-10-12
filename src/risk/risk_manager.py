"""
Risk Management Module

Manages position sizing, risk limits, and portfolio constraints.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime


class RiskManager:
    """Manage trading risk and position sizing."""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_position_size: float = 0.2,  # 20% of portfolio per position
        max_portfolio_risk: float = 0.02,  # 2% max risk per trade
        max_positions: int = 5,
        stop_loss_pct: float = 0.05,  # 5% stop loss
        max_daily_loss: float = 0.05  # 5% max daily loss
    ):
        """
        Initialize risk manager.
        
        Args:
            initial_capital: Initial capital
            max_position_size: Maximum position size as fraction of portfolio
            max_portfolio_risk: Maximum risk per trade as fraction of portfolio
            max_positions: Maximum number of concurrent positions
            stop_loss_pct: Stop loss percentage
            max_daily_loss: Maximum daily loss as fraction of portfolio
        """
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        self.max_daily_loss = max_daily_loss
        
        self.logger = logging.getLogger(__name__)
        
        # Track positions
        self.positions = {}
        self.daily_pnl = 0
        self.daily_start_value = initial_capital
        
    def calculate_position_size(
        self,
        entry_price: float,
        portfolio_value: float,
        volatility: Optional[float] = None
    ) -> float:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            entry_price: Entry price per share
            portfolio_value: Current portfolio value
            volatility: Price volatility (optional, for Kelly criterion)
        
        Returns:
            Position value in dollars
        """
        # Method 1: Fixed percentage of portfolio
        max_value_by_size = portfolio_value * self.max_position_size
        
        # Method 2: Risk-based sizing
        risk_amount = portfolio_value * self.max_portfolio_risk
        shares_by_risk = risk_amount / (entry_price * self.stop_loss_pct)
        max_value_by_risk = shares_by_risk * entry_price
        
        # Use the more conservative approach
        position_value = min(max_value_by_size, max_value_by_risk)
        
        # Ensure we don't exceed available capital
        position_value = min(position_value, portfolio_value * 0.95)
        
        self.logger.debug(f"Position sizing: ${position_value:.2f} "
                         f"(max by size: ${max_value_by_size:.2f}, "
                         f"max by risk: ${max_value_by_risk:.2f})")
        
        return position_value
    
    def can_open_position(self) -> bool:
        """Check if we can open a new position."""
        if len(self.positions) >= self.max_positions:
            self.logger.warning(f"Max positions reached: {len(self.positions)}/{self.max_positions}")
            return False
        
        # Check daily loss limit
        if self.daily_pnl < -self.daily_start_value * self.max_daily_loss:
            self.logger.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        
        return True
    
    def add_position(self, symbol: str, shares: int, entry_price: float):
        """Add a new position."""
        self.positions[symbol] = {
            'shares': shares,
            'entry_price': entry_price,
            'entry_value': shares * entry_price,
            'entry_date': datetime.now(),
            'stop_loss': entry_price * (1 - self.stop_loss_pct)
        }
        
        self.logger.info(f"Position added: {symbol} - {shares} shares @ ${entry_price:.2f}")
        self.logger.info(f"  Stop Loss: ${self.positions[symbol]['stop_loss']:.2f}")
    
    def remove_position(self, symbol: str):
        """Remove a position."""
        if symbol in self.positions:
            del self.positions[symbol]
            self.logger.info(f"Position removed: {symbol}")
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss is triggered.
        
        Args:
            symbol: Stock symbol
            current_price: Current price
        
        Returns:
            True if stop loss triggered
        """
        if symbol not in self.positions:
            return False
        
        stop_loss = self.positions[symbol]['stop_loss']
        
        if current_price <= stop_loss:
            self.logger.warning(f"STOP LOSS TRIGGERED for {symbol}: "
                              f"${current_price:.2f} <= ${stop_loss:.2f}")
            return True
        
        return False
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L tracking."""
        self.daily_pnl += pnl
        
        if self.daily_pnl < -self.daily_start_value * self.max_daily_loss:
            self.logger.critical(f"DAILY LOSS LIMIT REACHED: ${self.daily_pnl:.2f}")
    
    def reset_daily_tracking(self, current_portfolio_value: float):
        """Reset daily tracking (call at start of new trading day)."""
        self.daily_pnl = 0
        self.daily_start_value = current_portfolio_value
        self.logger.info(f"Daily tracking reset. Starting value: ${current_portfolio_value:,.2f}")
    
    def get_position_summary(self) -> Dict:
        """Get summary of current positions."""
        return {
            'total_positions': len(self.positions),
            'max_positions': self.max_positions,
            'positions': self.positions.copy(),
            'daily_pnl': self.daily_pnl,
            'max_daily_loss': self.max_daily_loss * self.daily_start_value
        }
    
    def calculate_portfolio_metrics(
        self,
        portfolio_value: float,
        positions_data: List[Dict]
    ) -> Dict:
        """
        Calculate portfolio-level risk metrics.
        
        Args:
            portfolio_value: Current portfolio value
            positions_data: List of position dictionaries with current prices
        
        Returns:
            Dictionary of risk metrics
        """
        if not positions_data:
            return {
                'total_exposure': 0,
                'exposure_pct': 0,
                'diversification': 1.0,
                'concentration_risk': 0
            }
        
        # Calculate total exposure
        total_exposure = sum(pos['market_value'] for pos in positions_data)
        exposure_pct = total_exposure / portfolio_value if portfolio_value > 0 else 0
        
        # Calculate concentration (Herfindahl index)
        weights = [pos['market_value'] / total_exposure for pos in positions_data]
        concentration = sum(w**2 for w in weights)
        diversification = 1 / concentration if concentration > 0 else 1.0
        
        # Find largest position
        max_position = max((pos['market_value'] / portfolio_value for pos in positions_data), default=0)
        
        return {
            'total_exposure': total_exposure,
            'exposure_pct': exposure_pct * 100,
            'diversification': diversification,
            'concentration_risk': concentration,
            'largest_position_pct': max_position * 100,
            'num_positions': len(positions_data)
        }
    
    def calculate_var(
        self,
        returns: pd.Series,
        confidence_level: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Series of historical returns
            confidence_level: Confidence level (e.g., 0.95 for 95%)
        
        Returns:
            VaR value
        """
        if len(returns) < 2:
            return 0.0
        
        var = np.percentile(returns, (1 - confidence_level) * 100)
        return abs(var)
    
    def calculate_sharpe_ratio(
        self,
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
        if len(returns) < 2:
            return 0.0
        
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        
        if excess_returns.std() == 0:
            return 0.0
        
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        return sharpe
    
    def check_margin_requirements(
        self,
        portfolio_value: float,
        buying_power: float,
        target_position_value: float
    ) -> bool:
        """
        Check if margin requirements are satisfied.
        
        Args:
            portfolio_value: Current portfolio value
            buying_power: Available buying power
            target_position_value: Value of position to open
        
        Returns:
            True if requirements are met
        """
        # Ensure we have enough buying power
        if target_position_value > buying_power:
            self.logger.warning(f"Insufficient buying power: "
                              f"Need ${target_position_value:.2f}, "
                              f"Have ${buying_power:.2f}")
            return False
        
        # Ensure position doesn't exceed maximum size
        if target_position_value > portfolio_value * self.max_position_size:
            self.logger.warning(f"Position exceeds max size: "
                              f"${target_position_value:.2f} > "
                              f"${portfolio_value * self.max_position_size:.2f}")
            return False
        
        return True
    
    def get_risk_report(self) -> str:
        """Generate a risk report."""
        report = [
            "\n" + "="*60,
            "RISK MANAGEMENT REPORT",
            "="*60,
            f"Maximum Position Size:    {self.max_position_size * 100:.1f}%",
            f"Maximum Portfolio Risk:   {self.max_portfolio_risk * 100:.1f}%",
            f"Maximum Positions:        {self.max_positions}",
            f"Stop Loss:                {self.stop_loss_pct * 100:.1f}%",
            f"Maximum Daily Loss:       {self.max_daily_loss * 100:.1f}%",
            f"\nCurrent Status:",
            f"  Active Positions:       {len(self.positions)}",
            f"  Daily P&L:              ${self.daily_pnl:,.2f}",
            f"  Available Position Slots: {self.max_positions - len(self.positions)}",
            "="*60
        ]
        return "\n".join(report)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    rm = RiskManager(initial_capital=100000)
    
    # Print risk parameters
    print(rm.get_risk_report())
    
    # Calculate position size
    position_size = rm.calculate_position_size(
        entry_price=150.0,
        portfolio_value=100000
    )
    print(f"\nRecommended position size: ${position_size:,.2f}")
    
    # Simulate adding positions
    rm.add_position('AAPL', 100, 150.0)
    rm.add_position('TSLA', 50, 200.0)
    
    # Check position summary
    summary = rm.get_position_summary()
    print(f"\nPosition Summary:")
    print(f"  Total Positions: {summary['total_positions']}/{summary['max_positions']}")
    print(f"  Daily P&L: ${summary['daily_pnl']:.2f}")
