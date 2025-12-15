"""
Portfolio analytics service for calculating performance metrics and reports.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import math
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.alpaca_client import AlpacaClient


class PortfolioAnalyticsService:
    """
    Service for calculating portfolio analytics and performance metrics.
    """
    
    def __init__(self, session: AsyncSession, broker: AlpacaClient):
        self.session = session
        self.broker = broker
    
    async def get_portfolio_summary(self, user_id: str) -> Dict:
        """
        Get current portfolio summary.
        Returns real-time portfolio state from broker.
        """
        # Get account info from broker
        account = await self.broker.get_account()
        
        # Get positions
        positions = await self.broker.get_positions()
        
        # Calculate position metrics
        num_long = sum(1 for p in positions if float(p.get('qty', 0)) > 0)
        num_short = sum(1 for p in positions if float(p.get('qty', 0)) < 0)
        
        return {
            "total_equity": float(account.get('equity', 0)),
            "cash_balance": float(account.get('cash', 0)),
            "positions_value": float(account.get('long_market_value', 0)) + abs(float(account.get('short_market_value', 0))),
            "daily_pnl": float(account.get('equity', 0)) - float(account.get('last_equity', 0)),
            "daily_return_pct": ((float(account.get('equity', 0)) / float(account.get('last_equity', 1))) - 1) * 100 if float(account.get('last_equity', 1)) > 0 else 0,
            "total_pnl": float(account.get('equity', 0)) - float(account.get('initial_equity', account.get('equity', 0))),
            "total_return_pct": ((float(account.get('equity', 0)) / float(account.get('initial_equity', 1))) - 1) * 100 if float(account.get('initial_equity', 1)) > 0 else 0,
            "num_positions": len(positions),
            "num_long_positions": num_long,
            "num_short_positions": num_short,
            "last_updated": datetime.utcnow()
        }
    
    async def get_equity_curve(self, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """
        Get equity curve data points for charting.
        
        Note: For now, this returns mock data. In production, this would:
        1. Query portfolio_snapshots table
        2. Calculate daily equity values
        3. Return time series data
        """
        # TODO: Replace with actual database query once models are deployed
        # from app.models.portfolio import PortfolioSnapshot
        # query = select(PortfolioSnapshot).where(
        #     and_(
        #         PortfolioSnapshot.user_id == user_id,
        #         PortfolioSnapshot.snapshot_date >= start_date,
        #         PortfolioSnapshot.snapshot_date <= end_date
        #     )
        # ).order_by(PortfolioSnapshot.snapshot_date)
        # result = await self.session.execute(query)
        # snapshots = result.scalars().all()
        
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Placeholder implementation
        account = await self.broker.get_account()
        current_equity = float(account.get('equity', 100000))
        
        # Generate sample data points (replace with real data from DB)
        data_points = []
        days = (end_date - start_date).days
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            # Simple linear progression (replace with actual historical data)
            equity = current_equity * (1 - 0.1 * ((days - i) / days))
            data_points.append({
                "date": date,
                "equity": equity,
                "daily_return": 0.0,
                "cumulative_return": ((equity / current_equity) - 1) * 100
            })
        
        return {
            "data_points": data_points,
            "start_date": start_date,
            "end_date": end_date,
            "total_points": len(data_points)
        }
    
    async def calculate_performance_metrics(self, user_id: str, period: str = "all_time") -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            user_id: User ID
            period: 'daily', 'weekly', 'monthly', 'yearly', 'all_time'
        
        Returns:
            Performance metrics including Sharpe ratio, max drawdown, win rate, etc.
        """
        # Define time window based on period
        end_date = datetime.utcnow()
        if period == "daily":
            start_date = end_date - timedelta(days=1)
        elif period == "weekly":
            start_date = end_date - timedelta(days=7)
        elif period == "monthly":
            start_date = end_date - timedelta(days=30)
        elif period == "yearly":
            start_date = end_date - timedelta(days=365)
        else:  # all_time
            start_date = end_date - timedelta(days=365 * 5)  # 5 years max
        
        # Get equity curve
        equity_data = await self.get_equity_curve(user_id, start_date, end_date)
        data_points = equity_data["data_points"]
        
        if len(data_points) < 2:
            return self._empty_metrics(period, start_date, end_date)
        
        # Calculate returns
        returns = []
        for i in range(1, len(data_points)):
            prev_equity = data_points[i-1]["equity"]
            curr_equity = data_points[i]["equity"]
            if prev_equity > 0:
                daily_return = (curr_equity - prev_equity) / prev_equity
                returns.append(daily_return)
        
        if not returns:
            return self._empty_metrics(period, start_date, end_date)
        
        # Calculate metrics
        total_return = (data_points[-1]["equity"] - data_points[0]["equity"]) / data_points[0]["equity"]
        total_return_pct = total_return * 100
        
        # Annualized return
        days_elapsed = len(returns)
        if days_elapsed > 0:
            annualized_return = ((1 + total_return) ** (252 / days_elapsed)) - 1
        else:
            annualized_return = 0
        
        # Volatility (standard deviation of returns)
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance) * math.sqrt(252)  # Annualized
        
        # Sharpe Ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02
        if volatility > 0:
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
            downside_deviation = math.sqrt(downside_variance) * math.sqrt(252)
            if downside_deviation > 0:
                sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation
            else:
                sortino_ratio = 0
        else:
            sortino_ratio = sharpe_ratio
        
        # Max Drawdown
        peak = data_points[0]["equity"]
        max_drawdown = 0
        max_drawdown_pct = 0
        current_drawdown = 0
        current_drawdown_pct = 0
        
        for point in data_points:
            equity = point["equity"]
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
            
            if point == data_points[-1]:
                current_drawdown = drawdown
                current_drawdown_pct = drawdown_pct
        
        # Calmar Ratio
        if max_drawdown_pct > 0:
            calmar_ratio = annualized_return / (max_drawdown_pct / 100)
        else:
            calmar_ratio = 0
        
        # Placeholder for trade statistics (would come from trades table)
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        win_rate = 0.0
        avg_win = 0.0
        avg_loss = 0.0
        profit_factor = 0.0
        
        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "annualized_return": annualized_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct,
            "current_drawdown": current_drawdown,
            "current_drawdown_pct": current_drawdown_pct,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "num_trades_long": 0,
            "num_trades_short": 0,
            "avg_holding_period_days": None,
            "benchmark_return": None,
            "benchmark_return_pct": None,
            "alpha": None,
            "beta": None
        }
    
    def _empty_metrics(self, period: str, start_date: datetime, end_date: datetime) -> Dict:
        """Return empty metrics structure."""
        return {
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "total_return": 0.0,
            "total_return_pct": 0.0,
            "annualized_return": 0.0,
            "volatility": None,
            "sharpe_ratio": None,
            "sortino_ratio": None,
            "calmar_ratio": None,
            "max_drawdown": None,
            "max_drawdown_pct": None,
            "current_drawdown": None,
            "current_drawdown_pct": None,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": None,
            "avg_win": None,
            "avg_loss": None,
            "profit_factor": None,
            "num_trades_long": 0,
            "num_trades_short": 0,
            "avg_holding_period_days": None,
            "benchmark_return": None,
            "benchmark_return_pct": None,
            "alpha": None,
            "beta": None
        }
    
    async def get_returns_analysis(self, user_id: str) -> Dict:
        """
        Get detailed returns breakdown (daily, weekly, monthly).
        """
        equity_data = await self.get_equity_curve(user_id)
        data_points = equity_data["data_points"]
        
        if len(data_points) < 2:
            return {
                "daily_returns": [],
                "weekly_returns": [],
                "monthly_returns": [],
                "best_day": 0.0,
                "worst_day": 0.0,
                "best_month": 0.0,
                "worst_month": 0.0,
                "positive_days": 0,
                "negative_days": 0,
                "avg_daily_return": 0.0
            }
        
        # Calculate daily returns
        daily_returns = []
        monthly_map = {}
        weekly_map = {}

        for i in range(1, len(data_points)):
            prev_equity = data_points[i-1]["equity"]
            curr_equity = data_points[i]["equity"]
            date = data_points[i]["date"]

            if prev_equity > 0:
                ret = ((curr_equity - prev_equity) / prev_equity)
                daily_returns.append(ret * 100)

                # Monthly Aggregation
                m_key = (date.year, date.month)
                if m_key not in monthly_map:
                    monthly_map[m_key] = 1.0
                monthly_map[m_key] *= (1 + ret)

                # Weekly Aggregation
                iso_cal = date.isocalendar()
                w_key = (iso_cal[0], iso_cal[1])
                if w_key not in weekly_map:
                    weekly_map[w_key] = 1.0
                weekly_map[w_key] *= (1 + ret)
        
        positive_days = sum(1 for r in daily_returns if r > 0)
        negative_days = sum(1 for r in daily_returns if r < 0)

        # Convert maps to lists (percentage)
        monthly_returns = [(val - 1) * 100 for key, val in sorted(monthly_map.items())]
        weekly_returns = [(val - 1) * 100 for key, val in sorted(weekly_map.items())]
        
        return {
            "daily_returns": daily_returns,
            "weekly_returns": weekly_returns,
            "monthly_returns": monthly_returns,
            "best_day": max(daily_returns) if daily_returns else 0.0,
            "worst_day": min(daily_returns) if daily_returns else 0.0,
            "best_month": max(monthly_returns) if monthly_returns else 0.0,
            "worst_month": min(monthly_returns) if monthly_returns else 0.0,
            "positive_days": positive_days,
            "negative_days": negative_days,
            "avg_daily_return": sum(daily_returns) / len(daily_returns) if daily_returns else 0.0
        }


async def get_portfolio_analytics_service(session: AsyncSession) -> PortfolioAnalyticsService:
    """Dependency injection for portfolio analytics service."""
    from app.integrations.alpaca_client import get_alpaca_client
    broker = get_alpaca_client()
    return PortfolioAnalyticsService(session, broker)
