"""
Visualization Module

Creates charts and graphs for trading analysis.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from datetime import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.gridspec import GridSpec
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib not installed. Install with: pip install matplotlib")


class Visualizer:
    """Create visualizations for trading analysis."""
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.
        
        Args:
            style: Matplotlib style to use
        """
        self.logger = logging.getLogger(__name__)
        
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("Matplotlib not available. Visualization disabled.")
            return
        
        try:
            plt.style.use(style)
        except:
            self.logger.warning(f"Style '{style}' not available, using default")
    
    def plot_price_with_signals(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        title: str = "Price Chart with Trading Signals",
        save_path: Optional[str] = None
    ):
        """
        Plot price chart with buy/sell signals.
        
        Args:
            data: DataFrame with OHLC data
            signals: Series with trading signals (1=buy, -1=sell, 0=hold)
            title: Chart title
            save_path: Path to save figure (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("Matplotlib not available")
            return
        
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot closing price
        ax.plot(data.index, data['close'], label='Close Price', linewidth=1.5, alpha=0.8)
        
        # Plot buy signals
        buy_signals = data[signals == 1]
        ax.scatter(buy_signals.index, buy_signals['close'], 
                  marker='^', color='green', s=100, label='Buy Signal', zorder=5)
        
        # Plot sell signals
        sell_signals = data[signals == -1]
        ax.scatter(sell_signals.index, sell_signals['close'],
                  marker='v', color='red', s=100, label='Sell Signal', zorder=5)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Chart saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_backtest_results(
        self,
        equity_curve: pd.Series,
        initial_capital: float,
        trades: List[Dict],
        title: str = "Backtest Results",
        save_path: Optional[str] = None
    ):
        """
        Plot comprehensive backtest results.
        
        Args:
            equity_curve: Series of portfolio values over time
            initial_capital: Initial capital
            trades: List of trade dictionaries
            title: Chart title
            save_path: Path to save figure (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("Matplotlib not available")
            return
        
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(3, 2, figure=fig)
        
        # 1. Equity Curve
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(equity_curve.index, equity_curve.values, 
                label='Portfolio Value', linewidth=2, color='blue')
        ax1.axhline(y=initial_capital, color='red', linestyle='--', 
                   label='Initial Capital', linewidth=1)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=11)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # 2. Drawdown
        ax2 = fig.add_subplot(gs[1, :])
        cumulative_max = equity_curve.expanding().max()
        drawdown = (equity_curve - cumulative_max) / cumulative_max * 100
        ax2.fill_between(drawdown.index, drawdown.values, 0, 
                         alpha=0.3, color='red', label='Drawdown')
        ax2.plot(drawdown.index, drawdown.values, color='darkred', linewidth=1)
        ax2.set_ylabel('Drawdown (%)', fontsize=11)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # 3. Trade P&L Distribution
        ax3 = fig.add_subplot(gs[2, 0])
        if trades:
            profits = [t['profit'] for t in trades]
            ax3.hist(profits, bins=20, alpha=0.7, color='steelblue', edgecolor='black')
            ax3.axvline(x=0, color='red', linestyle='--', linewidth=1)
            ax3.set_xlabel('Profit/Loss ($)', fontsize=11)
            ax3.set_ylabel('Frequency', fontsize=11)
            ax3.set_title('Trade P&L Distribution', fontsize=11, fontweight='bold')
            ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Win/Loss Pie Chart
        ax4 = fig.add_subplot(gs[2, 1])
        if trades:
            winning_trades = sum(1 for t in trades if t['profit'] > 0)
            losing_trades = sum(1 for t in trades if t['profit'] < 0)
            
            if winning_trades + losing_trades > 0:
                sizes = [winning_trades, losing_trades]
                colors = ['green', 'red']
                labels = [f'Winning\n({winning_trades})', f'Losing\n({losing_trades})']
                explode = (0.05, 0.05)
                
                ax4.pie(sizes, explode=explode, labels=labels, colors=colors,
                       autopct='%1.1f%%', shadow=True, startangle=90)
                ax4.set_title('Win/Loss Ratio', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Chart saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_strategy_comparison(
        self,
        results: Dict[str, pd.Series],
        title: str = "Strategy Comparison",
        save_path: Optional[str] = None
    ):
        """
        Compare multiple strategies.
        
        Args:
            results: Dictionary of strategy names to equity curves
            title: Chart title
            save_path: Path to save figure (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("Matplotlib not available")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot equity curves
        for strategy_name, equity_curve in results.items():
            ax1.plot(equity_curve.index, equity_curve.values, 
                    label=strategy_name, linewidth=2, alpha=0.8)
        
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)', fontsize=11)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Plot returns
        for strategy_name, equity_curve in results.items():
            returns = equity_curve.pct_change() * 100
            ax2.plot(returns.index, returns.values, 
                    label=strategy_name, linewidth=1, alpha=0.7)
        
        ax2.set_xlabel('Date', fontsize=11)
        ax2.set_ylabel('Daily Returns (%)', fontsize=11)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Chart saved to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_correlation_matrix(
        self,
        data: pd.DataFrame,
        title: str = "Correlation Matrix",
        save_path: Optional[str] = None
    ):
        """
        Plot correlation matrix heatmap.
        
        Args:
            data: DataFrame with multiple time series
            title: Chart title
            save_path: Path to save figure (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("Matplotlib not available")
            return
        
        try:
            import seaborn as sns
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Calculate correlation matrix
            corr_matrix = data.corr()
            
            # Create heatmap
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                       center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                       ax=ax)
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except ImportError:
            self.logger.warning("Seaborn not installed. Using basic heatmap.")
            
            fig, ax = plt.subplots(figsize=(10, 8))
            corr_matrix = data.corr()
            
            im = ax.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr_matrix.columns)))
            ax.set_yticks(range(len(corr_matrix.columns)))
            ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
            ax.set_yticklabels(corr_matrix.columns)
            
            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Correlation', rotation=270, labelpad=15)
            
            ax.set_title(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"Chart saved to {save_path}")
            else:
                plt.show()
            
            plt.close()
    
    def plot_portfolio_allocation(
        self,
        positions: Dict[str, float],
        title: str = "Portfolio Allocation",
        save_path: Optional[str] = None
    ):
        """
        Plot portfolio allocation pie chart.
        
        Args:
            positions: Dictionary of symbol to market value
            title: Chart title
            save_path: Path to save figure (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            self.logger.error("Matplotlib not available")
            return
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Prepare data
        symbols = list(positions.keys())
        values = list(positions.values())
        total = sum(values)
        
        if total == 0:
            self.logger.warning("No positions to plot")
            return
        
        # Create colors
        colors = plt.cm.Set3(range(len(symbols)))
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=symbols,
            colors=colors,
            autopct=lambda pct: f'{pct:.1f}%\n${pct * total / 100:.2f}',
            shadow=True,
            startangle=90
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Chart saved to {save_path}")
        else:
            plt.show()
        
        plt.close()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    viz = Visualizer()
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100)
    prices = pd.DataFrame({
        'close': 100 + np.cumsum(np.random.randn(100)),
        'open': 100 + np.cumsum(np.random.randn(100)),
        'high': 100 + np.cumsum(np.random.randn(100)),
        'low': 100 + np.cumsum(np.random.randn(100))
    }, index=dates)
    
    # Create sample signals
    signals = pd.Series([0] * 100, index=dates)
    signals.iloc[10] = 1  # Buy
    signals.iloc[50] = -1  # Sell
    
    print("Visualizer initialized. Example charts can be generated.")
    print("Use plot_price_with_signals(), plot_backtest_results(), etc.")
