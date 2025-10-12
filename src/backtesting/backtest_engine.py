"""
Backtesting Engine

Simulates trading strategies on historical data to evaluate performance.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime

import sys
sys.path.append('../..')

from src.strategies.base_strategy import BaseStrategy, StrategyMetrics
from src.data.data_fetcher import DataFetcher


class BacktestEngine:
    """Backtest trading strategies on historical data."""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000,
        commission: float = 0.001,
        slippage: float = 0.0005
    ):
        """
        Initialize backtesting engine.
        
        Args:
            strategy: Trading strategy to backtest
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital
            commission: Commission rate per trade
            slippage: Slippage rate per trade
        """
        self.strategy = strategy
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.trades = []
        self.equity_curve = None
        self.portfolio_history = None
        self.metrics = {}
        
    def run(self) -> Dict:
        """
        Run backtest simulation.
        
        Returns:
            Dictionary with backtest results
        """
        self.logger.info(f"Starting backtest for {self.symbol}")
        self.logger.info(f"Period: {self.start_date} to {self.end_date}")
        self.logger.info(f"Strategy: {self.strategy}")
        
        # Fetch historical data
        fetcher = DataFetcher()
        data = fetcher.fetch_historical_data(
            self.symbol,
            self.start_date,
            self.end_date
        )
        
        if data.empty:
            self.logger.error("No data available for backtesting")
            return {}
        
        self.logger.info(f"Loaded {len(data)} data points")
        
        # Generate signals
        signals = self.strategy.generate_signals(data)
        
        # Simulate trading
        self._simulate_trading(data, signals)
        
        # Calculate metrics
        self._calculate_metrics()
        
        self.logger.info("Backtest completed")
        
        return self.get_results()
    
    def _simulate_trading(self, data: pd.DataFrame, signals: pd.Series):
        """Simulate trading based on signals."""
        
        # Initialize portfolio
        cash = self.initial_capital
        position = 0  # Number of shares
        portfolio_value = []
        
        # Track trades
        entry_price = None
        entry_date = None
        
        for date, row in data.iterrows():
            signal = signals.loc[date]
            current_price = row['close']
            
            # Execute trades based on signals
            if signal == 1 and position == 0:  # BUY signal
                # Calculate position size (use 100% of available cash for simplicity)
                shares_to_buy = int(cash / (current_price * (1 + self.commission + self.slippage)))
                
                if shares_to_buy > 0:
                    cost = shares_to_buy * current_price * (1 + self.commission + self.slippage)
                    
                    if cost <= cash:
                        position = shares_to_buy
                        cash -= cost
                        entry_price = current_price
                        entry_date = date
                        
                        self.logger.debug(f"BUY {shares_to_buy} shares at ${current_price:.2f} on {date}")
            
            elif signal == -1 and position > 0:  # SELL signal
                # Sell all shares
                proceeds = position * current_price * (1 - self.commission - self.slippage)
                profit = proceeds - (position * entry_price * (1 + self.commission + self.slippage))
                profit_pct = (profit / (position * entry_price)) * 100
                
                # Record trade
                self.trades.append({
                    'entry_date': entry_date,
                    'exit_date': date,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'shares': position,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'duration': (date - entry_date).days
                })
                
                cash += proceeds
                position = 0
                entry_price = None
                entry_date = None
                
                self.logger.debug(f"SELL {position} shares at ${current_price:.2f} on {date}, "
                                f"Profit: ${profit:.2f} ({profit_pct:.2f}%)")
            
            # Calculate portfolio value
            current_portfolio_value = cash + (position * current_price)
            portfolio_value.append(current_portfolio_value)
        
        # Close any open position at the end
        if position > 0:
            final_price = data.iloc[-1]['close']
            proceeds = position * final_price * (1 - self.commission - self.slippage)
            profit = proceeds - (position * entry_price * (1 + self.commission + self.slippage))
            profit_pct = (profit / (position * entry_price)) * 100
            
            self.trades.append({
                'entry_date': entry_date,
                'exit_date': data.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'shares': position,
                'profit': profit,
                'profit_pct': profit_pct,
                'duration': (data.index[-1] - entry_date).days
            })
            
            cash += proceeds
            position = 0
        
        # Store equity curve
        self.equity_curve = pd.Series(portfolio_value, index=data.index)
        
        # Calculate final portfolio value
        final_value = cash + (position * data.iloc[-1]['close'])
        self.logger.info(f"Final portfolio value: ${final_value:,.2f}")
        self.logger.info(f"Total return: {((final_value / self.initial_capital) - 1) * 100:.2f}%")
        self.logger.info(f"Total trades: {len(self.trades)}")
    
    def _calculate_metrics(self):
        """Calculate performance metrics."""
        
        if self.equity_curve is None or len(self.trades) == 0:
            self.logger.warning("No trades to analyze")
            return
        
        # Calculate returns
        total_return = StrategyMetrics.calculate_returns(self.equity_curve)
        
        # Calculate daily returns
        daily_returns = self.equity_curve.pct_change().dropna()
        
        # Sharpe ratio
        sharpe = StrategyMetrics.calculate_sharpe_ratio(daily_returns)
        
        # Max drawdown
        max_dd = StrategyMetrics.calculate_max_drawdown(self.equity_curve)
        
        # Win rate
        win_rate = StrategyMetrics.calculate_win_rate(self.trades)
        
        # Profit factor
        profit_factor = StrategyMetrics.calculate_profit_factor(self.trades)
        
        # Average trade metrics
        profits = [t['profit'] for t in self.trades]
        avg_profit = np.mean(profits)
        avg_win = np.mean([p for p in profits if p > 0]) if any(p > 0 for p in profits) else 0
        avg_loss = np.mean([p for p in profits if p < 0]) if any(p < 0 for p in profits) else 0
        
        # Store metrics
        self.metrics = {
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd * 100,
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'profit_factor': profit_factor,
            'total_trades': len(self.trades),
            'winning_trades': sum(1 for t in self.trades if t['profit'] > 0),
            'losing_trades': sum(1 for t in self.trades if t['profit'] < 0),
            'avg_profit': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_value': self.equity_curve.iloc[-1],
            'initial_capital': self.initial_capital
        }
    
    def get_results(self) -> Dict:
        """Get backtest results."""
        return {
            'metrics': self.metrics,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'strategy': str(self.strategy),
            'symbol': self.symbol,
            'period': f"{self.start_date} to {self.end_date}"
        }
    
    def print_results(self):
        """Print backtest results."""
        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {self.strategy}")
        print("="*60)
        print(f"Symbol: {self.symbol}")
        print(f"Period: {self.start_date} to {self.end_date}")
        
        if not self.metrics:
            print("\n⚠️  No results available. Backtest may have failed.")
            print("="*60 + "\n")
            return
        
        print(f"\nPerformance Metrics:")
        print(f"  Initial Capital:    ${self.metrics['initial_capital']:,.2f}")
        print(f"  Final Value:        ${self.metrics['final_value']:,.2f}")
        print(f"  Total Return:       {self.metrics['total_return_pct']:.2f}%")
        print(f"  Sharpe Ratio:       {self.metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown:       {self.metrics['max_drawdown_pct']:.2f}%")
        print(f"\nTrade Statistics:")
        print(f"  Total Trades:       {self.metrics['total_trades']}")
        print(f"  Winning Trades:     {self.metrics['winning_trades']}")
        print(f"  Losing Trades:      {self.metrics['losing_trades']}")
        print(f"  Win Rate:           {self.metrics['win_rate_pct']:.2f}%")
        print(f"  Profit Factor:      {self.metrics['profit_factor']:.2f}")
        print(f"  Avg Profit/Trade:   ${self.metrics['avg_profit']:.2f}")
        print(f"  Avg Win:            ${self.metrics['avg_win']:.2f}")
        print(f"  Avg Loss:           ${self.metrics['avg_loss']:.2f}")
        print("="*60 + "\n")
    
    def plot_results(self):
        """Plot backtest results."""
        try:
            import matplotlib.pyplot as plt
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # Plot equity curve
            ax1.plot(self.equity_curve.index, self.equity_curve.values, label='Portfolio Value')
            ax1.axhline(y=self.initial_capital, color='r', linestyle='--', label='Initial Capital')
            ax1.set_title(f'Backtest Results: {self.strategy} on {self.symbol}')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Portfolio Value ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot drawdown
            cumulative_max = self.equity_curve.expanding().max()
            drawdown = (self.equity_curve - cumulative_max) / cumulative_max
            ax2.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
            ax2.set_title('Drawdown')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Drawdown (%)')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            self.logger.warning("Matplotlib not installed. Cannot plot results.")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    from src.strategies.sma_crossover import SMACrossoverStrategy
    
    # Initialize strategy
    strategy = SMACrossoverStrategy(short_window=50, long_window=200)
    
    # Run backtest
    engine = BacktestEngine(
        strategy=strategy,
        symbol='AAPL',
        start_date='2023-01-01',
        end_date='2024-01-01',
        initial_capital=100000
    )
    
    results = engine.run()
    engine.print_results()
    
    # Uncomment to plot results
    # engine.plot_results()
