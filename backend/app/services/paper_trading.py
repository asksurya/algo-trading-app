"""
Paper trading service for simulated trading with virtual money.
"""
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade


class PaperTradingService:
    """
    Service for paper trading simulation.
    Manages virtual portfolio without affecting real broker account.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def initialize_paper_account(self, user_id: str, starting_balance: float = 100000.0) -> Dict:
        """
        Initialize a paper trading account for a user.
        
        Args:
            user_id: User ID
            starting_balance: Initial virtual cash balance
        
        Returns:
            Paper account details
        """
        # Check if account exists
        stmt = select(PaperAccount).where(PaperAccount.user_id == user_id).options(
            selectinload(PaperAccount.positions),
            selectinload(PaperAccount.trades)
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            account = PaperAccount(
                user_id=user_id,
                cash_balance=starting_balance,
                initial_balance=starting_balance
            )
            self.session.add(account)
            await self.session.commit()
            await self.session.refresh(account)
        
        return self._format_account(account)
    
    async def get_paper_account(self, user_id: str) -> Optional[Dict]:
        """Get paper account details."""
        stmt = select(PaperAccount).where(PaperAccount.user_id == user_id).options(
            selectinload(PaperAccount.positions),
            selectinload(PaperAccount.trades)
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()

        if not account:
            return await self.initialize_paper_account(user_id)

        return self._format_account(account)
    
    async def reset_paper_account(self, user_id: str, starting_balance: float = 100000.0) -> Dict:
        """
        Reset paper account to initial state.
        Clears all positions, orders, and trades.
        """
        stmt = select(PaperAccount).where(PaperAccount.user_id == user_id)
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()

        if account:
            await self.session.delete(account)
            await self.session.commit()

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
        stmt = select(PaperAccount).where(PaperAccount.user_id == user_id).options(
            selectinload(PaperAccount.positions)
        )
        result = await self.session.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            await self.initialize_paper_account(user_id)
            # Re-fetch
            result = await self.session.execute(stmt)
            account = result.scalar_one()

        # Get current market price (would call real broker API)
        # For now, use placeholder price
        current_price = limit_price if limit_price else 100.0  # Placeholder
        
        # Calculate order value
        order_value = qty * current_price
        
        # Validate order
        if side == 'buy':
            if order_value > account.cash_balance:
                return {
                    "success": False,
                    "error": "Insufficient buying power",
                    "required": order_value,
                    "available": account.cash_balance
                }
            
            # Execute buy
            account.cash_balance -= order_value
            
            # Update or create position
            # Find existing position for symbol
            position = next((p for p in account.positions if p.symbol == symbol), None)

            if position:
                total_qty = position.qty + qty
                total_cost = (position.qty * position.avg_price) + (qty * current_price)
                avg_price = total_cost / total_qty
                
                position.qty = total_qty
                position.avg_price = avg_price
                position.market_value = total_qty * current_price
            else:
                position = PaperPosition(
                    account_id=account.id,
                    symbol=symbol,
                    qty=qty,
                    avg_price=current_price,
                    market_value=qty * current_price,
                    unrealized_pnl=0.0
                )
                account.positions.append(position)
        
        elif side == 'sell':
            position = next((p for p in account.positions if p.symbol == symbol), None)

            if not position or position.qty < qty:
                return {
                    "success": False,
                    "error": "Insufficient shares to sell",
                    "requested": qty,
                    "available": position.qty if position else 0
                }
            
            # Execute sell
            realized_pnl = (current_price - position.avg_price) * qty
            account.cash_balance += order_value
            account.total_pnl = (account.total_pnl or 0.0) + realized_pnl
            
            # Update position
            position.qty -= qty
            if position.qty == 0:
                await self.session.delete(position)
                # Remove from local list to reflect deletion
                account.positions.remove(position)
            else:
                position.market_value = position.qty * current_price

        
        # Record trade
        trade = PaperTrade(
            account_id=account.id,
            symbol=symbol,
            qty=qty,
            side=side,
            price=current_price,
            value=order_value,
            timestamp=datetime.utcnow()
        )
        self.session.add(trade)
        
        # Calculate total return
        positions_value = sum(
            p.qty * current_price for p in account.positions
        )
        total_equity = account.cash_balance + positions_value
        account.total_return_pct = ((total_equity / account.initial_balance) - 1) * 100
        
        await self.session.commit()
        await self.session.refresh(account)

        return {
            "success": True,
            "trade": {
                "symbol": trade.symbol,
                "qty": trade.qty,
                "side": trade.side,
                "price": trade.price,
                "value": trade.value,
                "timestamp": trade.timestamp
            },
            "account": {
                "cash_balance": account.cash_balance,
                "total_equity": total_equity,
                "total_pnl": account.total_pnl,
                "total_return_pct": account.total_return_pct
            }
        }
    
    async def get_paper_positions(self, user_id: str) -> List[Dict]:
        """Get all paper trading positions."""
        stmt = select(PaperPosition).join(PaperAccount).where(PaperAccount.user_id == user_id)
        result = await self.session.execute(stmt)
        positions = result.scalars().all()

        return [
            {
                "symbol": pos.symbol,
                "qty": pos.qty,
                "avg_price": pos.avg_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl
            }
            for pos in positions
        ]
    
    async def get_paper_trade_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get paper trading trade history."""
        stmt = select(PaperTrade).join(PaperAccount).where(
            PaperAccount.user_id == user_id
        ).order_by(desc(PaperTrade.timestamp)).limit(limit)

        result = await self.session.execute(stmt)
        trades = result.scalars().all()

        return [
            {
                "symbol": t.symbol,
                "qty": t.qty,
                "side": t.side,
                "price": t.price,
                "value": t.value,
                "timestamp": t.timestamp
            }
            for t in trades
        ]

    def _format_account(self, account: PaperAccount) -> Dict:
        """Helper to format account model to dictionary."""
        positions_dict = {}
        # Recalculate positions value and pnl if possible?
        # For now return stored values
        for pos in account.positions:
            positions_dict[pos.symbol] = {
                'qty': pos.qty,
                'avg_price': pos.avg_price,
                'market_value': pos.market_value,
                'unrealized_pnl': pos.unrealized_pnl
            }

        trades_list = [
            {
                "symbol": t.symbol,
                "qty": t.qty,
                "side": t.side,
                "price": t.price,
                "value": t.value,
                "timestamp": t.timestamp
            }
            for t in sorted(account.trades, key=lambda x: x.timestamp)
        ]

        return {
            "user_id": account.user_id,
            "cash_balance": account.cash_balance,
            "initial_balance": account.initial_balance,
            "positions": positions_dict,
            "orders": [], # Orders not persisted separately yet
            "trades": trades_list,
            "created_at": account.created_at,
            "total_pnl": account.total_pnl,
            "total_return_pct": account.total_return_pct
        }


async def get_paper_trading_service(session: AsyncSession = None) -> PaperTradingService:
    """Get paper trading service instance."""
    return PaperTradingService(session)
