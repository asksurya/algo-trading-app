"""
Paper trading service for simulated trading with virtual money.
"""
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.integrations.broker import AlpacaBroker


class PaperTradingService:
    """
    Service for paper trading simulation.
    Manages virtual portfolio without affecting real broker account.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.paper_accounts = {}  # In-memory paper accounts (TODO: move to DB)
    
    async def initialize_paper_account(self, user_id: str, starting_balance: float = 100000.0) -> Dict:
        """
        Initialize a paper trading account for a user.
        
        Args:
            user_id: User ID
            starting_balance: Initial virtual cash balance
        
        Returns:
            Paper account details
        """
        # TODO: Store in database once models are deployed
        # For now, use in-memory storage
        self.paper_accounts[user_id] = {
            "user_id": user_id,
            "cash_balance": starting_balance,
            "initial_balance": starting_balance,
            "positions": {},  # symbol -> {qty, avg_price, market_value, unrealized_pnl}
            "orders": [],
            "trades": [],
            "created_at": datetime.utcnow(),
            "total_pnl": 0.0,
            "total_return_pct": 0.0
        }
        
        return self.paper_accounts[user_id]
    
    async def get_paper_account(self, user_id: str) -> Optional[Dict]:
        """Get paper account details."""
        if user_id not in self.paper_accounts:
            # Initialize if doesn't exist
            return await self.initialize_paper_account(user_id)
        return self.paper_accounts[user_id]
    
    async def reset_paper_account(self, user_id: str, starting_balance: float = 100000.0) -> Dict:
        """
        Reset paper account to initial state.
        Clears all positions, orders, and trades.
        """
        return await self.initialize_paper_account(user_id, starting_balance)
    
    async def execute_paper_order(
        self,
        user_id: str,
        symbol: str,
        qty: float,
        side: str,  # 'buy' or 'sell'
        order_type: str = 'market',
        limit_price: Optional[float] = None
    ) -> Dict:
        """
        Execute a simulated order in paper trading.
        
        Args:
            user_id: User ID
            symbol: Stock symbol
            qty: Quantity
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', etc.
            limit_price: Price for limit orders
        
        Returns:
            Order execution result
        """
        account = await self.get_paper_account(user_id)
        
        # Get current market price (would call real broker API)
        # For now, use placeholder price
        current_price = limit_price if limit_price else 100.0  # Placeholder
        
        # Calculate order value
        order_value = qty * current_price
        
        # Validate order
        if side == 'buy':
            if order_value > account['cash_balance']:
                return {
                    "success": False,
                    "error": "Insufficient buying power",
                    "required": order_value,
                    "available": account['cash_balance']
                }
            
            # Execute buy
            account['cash_balance'] -= order_value
            
            # Update or create position
            if symbol in account['positions']:
                pos = account['positions'][symbol]
                total_qty = pos['qty'] + qty
                total_cost = (pos['qty'] * pos['avg_price']) + (qty * current_price)
                avg_price = total_cost / total_qty
                
                pos['qty'] = total_qty
                pos['avg_price'] = avg_price
            else:
                account['positions'][symbol] = {
                    'qty': qty,
                    'avg_price': current_price,
                    'market_value': qty * current_price,
                    'unrealized_pnl': 0.0
                }
        
        elif side == 'sell':
            if symbol not in account['positions'] or account['positions'][symbol]['qty'] < qty:
                return {
                    "success": False,
                    "error": "Insufficient shares to sell",
                    "requested": qty,
                    "available": account['positions'].get(symbol, {}).get('qty', 0)
                }
            
            # Execute sell
            pos = account['positions'][symbol]
            realized_pnl = (current_price - pos['avg_price']) * qty
            account['cash_balance'] += order_value
            account['total_pnl'] += realized_pnl
            
            # Update position
            pos['qty'] -= qty
            if pos['qty'] == 0:
                del account['positions'][symbol]
        
        # Record trade
        trade = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "price": current_price,
            "value": order_value,
            "timestamp": datetime.utcnow()
        }
        account['trades'].append(trade)
        
        # Calculate total return
        total_equity = account['cash_balance'] + sum(
            p['qty'] * current_price for p in account['positions'].values()
        )
        account['total_return_pct'] = ((total_equity / account['initial_balance']) - 1) * 100
        
        return {
            "success": True,
            "trade": trade,
            "account": {
                "cash_balance": account['cash_balance'],
                "total_equity": total_equity,
                "total_pnl": account['total_pnl'],
                "total_return_pct": account['total_return_pct']
            }
        }
    
    async def get_paper_positions(self, user_id: str) -> List[Dict]:
        """Get all paper trading positions."""
        account = await self.get_paper_account(user_id)
        return [
            {"symbol": symbol, **details}
            for symbol, details in account['positions'].items()
        ]
    
    async def get_paper_trade_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get paper trading trade history."""
        account = await self.get_paper_account(user_id)
        return account['trades'][-limit:]


# Singleton instance
_paper_trading_service = None


async def get_paper_trading_service(session: AsyncSession = None) -> PaperTradingService:
    """Get paper trading service instance."""
    global _paper_trading_service
    if _paper_trading_service is None:
        _paper_trading_service = PaperTradingService(session)
    return _paper_trading_service
