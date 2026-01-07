"""
Paper trading service for simulated trading with virtual money.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from app.models.paper_trading import PaperAccount, PaperPosition, PaperTrade
from app.integrations.market_data import get_market_data_service


class PaperTradingService:
    """
    Service for paper trading simulation.
    Manages virtual portfolio without affecting real broker account.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.market_data = get_market_data_service()
    
    async def initialize_paper_account(self, user_id: str, starting_balance: float = 100000.0) -> Dict[str, Any]:
        """
        Initialize a paper trading account for a user.
        """
        # Check if account already exists
        result = await self.session.execute(
            select(PaperAccount)
            .where(PaperAccount.user_id == user_id)
            .options(selectinload(PaperAccount.positions), selectinload(PaperAccount.trades))
        )
        account = result.scalar_one_or_none()
        
        if account:
            return await self._format_account_async(account)

        # Create new account
        account = PaperAccount(
            user_id=user_id,
            cash_balance=starting_balance,
            initial_balance=starting_balance,
            total_pnl=0.0,
            total_return_pct=0.0
        )
        self.session.add(account)
        await self.session.commit()

        # After commit, the object is expired. We must not access attributes directly.
        # We need to re-query to get the fresh state with relationships loaded.
        return await self.get_paper_account(user_id)
    
    async def get_paper_account(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get paper account details."""
        result = await self.session.execute(
            select(PaperAccount)
            .where(PaperAccount.user_id == user_id)
            .options(selectinload(PaperAccount.positions), selectinload(PaperAccount.trades))
        )
        account = result.scalar_one_or_none()

        if not account:
            return await self.initialize_paper_account(user_id)

        return await self._format_account_async(account)
    
    async def _format_account_async(self, account: PaperAccount) -> Dict[str, Any]:
        """
        Format account object to dictionary using real-time prices.
        Assumes account has relationships loaded and is not expired.
        """
        positions_dict = {}
        symbols = [pos.symbol for pos in account.positions]

        # Fetch real-time prices if there are positions
        current_prices = {}
        if symbols:
            try:
                trades_data = await self.market_data.get_multi_trades(symbols)
                for trade in trades_data:
                    current_prices[trade["symbol"]] = trade["price"]
            except Exception as e:
                # Log error and fallback to avg_price will happen below
                # Assuming logging is configured
                print(f"Error fetching prices: {e}")

        # Iterate over eager-loaded collection
        for pos in account.positions:
            # Use real-time price if available, otherwise fallback to avg_price
            current_price = current_prices.get(pos.symbol, pos.avg_price)

            market_value = pos.qty * current_price
            unrealized_pnl = market_value - (pos.qty * pos.avg_price)

            positions_dict[pos.symbol] = {
                'qty': pos.qty,
                'avg_price': pos.avg_price,
                'current_price': current_price,
                'market_value': market_value,
                'unrealized_pnl': unrealized_pnl
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
            for t in account.trades
        ]

        # Calculate total equity using current market values
        total_positions_value = sum(p['market_value'] for p in positions_dict.values())
        total_equity = account.cash_balance + total_positions_value

        # Recalculate total return based on current equity
        total_return_pct = 0.0
        if account.initial_balance > 0:
            total_return_pct = ((total_equity / account.initial_balance) - 1) * 100

        return {
            "user_id": account.user_id,
            "cash_balance": account.cash_balance,
            "initial_balance": account.initial_balance,
            "total_equity": total_equity,
            "positions": positions_dict,
            "orders": [], # Keeping for compatibility
            "trades": trades_list,
            "created_at": account.created_at,
            "total_pnl": account.total_pnl, # Realized PnL
            "unrealized_pnl": total_positions_value - sum(p['qty'] * p['avg_price'] for p in positions_dict.values()),
            "total_return_pct": total_return_pct
        }

    async def reset_paper_account(self, user_id: str, starting_balance: float = 100000.0) -> Dict[str, Any]:
        """
        Reset paper account to initial state.
        """
        # Find account
        result = await self.session.execute(
            select(PaperAccount).where(PaperAccount.user_id == user_id)
        )
        account = result.scalar_one_or_none()

        if account:
            account_id = account.id

            # Delete associated positions and trades
            await self.session.execute(
                delete(PaperPosition).where(PaperPosition.account_id == account_id)
            )
            await self.session.execute(
                delete(PaperTrade).where(PaperTrade.account_id == account_id)
            )

            # Reset account fields
            account.cash_balance = starting_balance
            account.initial_balance = starting_balance
            account.total_pnl = 0.0
            account.total_return_pct = 0.0

            await self.session.commit()

            # Re-fetch fully
            return await self.get_paper_account(user_id)
        else:
            return await self.initialize_paper_account(user_id, starting_balance)
    
    async def execute_paper_order(
        self,
        user_id: str,
        symbol: str,
        qty: float,
        side: str,  # 'buy' or 'sell'
        order_type: str = 'market',
        limit_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a simulated order.
        """
        # 1. Fetch Account (Single Query)
        result = await self.session.execute(
            select(PaperAccount)
            .where(PaperAccount.user_id == user_id)
            .options(selectinload(PaperAccount.positions))
        )
        account = result.scalar_one_or_none()
        
        if not account:
            # Initialize returns a fresh dict, but we need the object for updates.
            # So initialize then re-query.
            await self.initialize_paper_account(user_id)
            result = await self.session.execute(
                select(PaperAccount)
                .where(PaperAccount.user_id == user_id)
                .options(selectinload(PaperAccount.positions))
            )
            account = result.scalar_one()
        
        # 2. Logic Check
        # For market orders, we should really fetch current price here too!
        if limit_price:
            current_price = limit_price
        else:
             # Fetch real time price for execution
            try:
                trade_data = await self.market_data.get_latest_trade(symbol)
                current_price = trade_data['price']
            except Exception as e:
                # In production, this should fail if price is unavailable
                return {
                    "success": False,
                    "error": f"Failed to fetch market price for {symbol}: {str(e)}"
                }

        order_value = qty * current_price
        
        # Capture initial state for response if failure
        current_cash = account.cash_balance

        if side == 'buy':
            if order_value > current_cash:
                return {
                    "success": False,
                    "error": "Insufficient buying power",
                    "required": order_value,
                    "available": current_cash
                }
            
            account.cash_balance -= order_value

            # Update Position
            # We already eager loaded positions, so we can check in memory
            # OR query specific position. Querying is safer for concurrency usually,
            # but here we are in a transaction.
            
            pos_result = await self.session.execute(
                select(PaperPosition)
                .where(and_(PaperPosition.account_id == account.id, PaperPosition.symbol == symbol))
            )
            pos = pos_result.scalar_one_or_none()

            if pos:
                total_qty = pos.qty + qty
                total_cost = (pos.qty * pos.avg_price) + (qty * current_price)
                avg_price = total_cost / total_qty
                
                pos.qty = total_qty
                pos.avg_price = avg_price
            else:
                pos = PaperPosition(
                    account_id=account.id,
                    symbol=symbol,
                    qty=qty,
                    avg_price=current_price
                )
                self.session.add(pos)
        
        elif side == 'sell':
            pos_result = await self.session.execute(
                select(PaperPosition)
                .where(and_(PaperPosition.account_id == account.id, PaperPosition.symbol == symbol))
            )
            pos = pos_result.scalar_one_or_none()

            if not pos or pos.qty < qty:
                return {
                    "success": False,
                    "error": "Insufficient shares to sell",
                    "requested": qty,
                    "available": pos.qty if pos else 0
                }
            
            realized_pnl = (current_price - pos.avg_price) * qty
            account.cash_balance += order_value
            account.total_pnl += realized_pnl
            
            pos.qty -= qty
            if pos.qty <= 0:
                await self.session.delete(pos)

        # 3. Create Trade Record
        timestamp = datetime.utcnow()
        trade = PaperTrade(
            account_id=account.id,
            symbol=symbol,
            qty=qty,
            side=side,
            price=current_price,
            value=order_value,
            timestamp=timestamp
        )
        self.session.add(trade)

        # 4. Commit Transaction
        await self.session.commit()

        # 5. Re-query for Final State Calculation
        # We need the fresh list of positions to calculate total equity.
        # Everything is expired now, so we MUST start a new query.

        # To be safe, let's use user_id which we have from args
        # IMPORTANT: Load both positions AND trades to avoid lazy loading errors
        result_final = await self.session.execute(
             select(PaperAccount)
            .where(PaperAccount.user_id == user_id)
            .options(
                selectinload(PaperAccount.positions),
                selectinload(PaperAccount.trades)
            )
        )
        account_final = result_final.scalar_one()

        # Calculate Totals from Fresh Data
        # Re-fetch prices if needed, or re-use execution price?
        # For simplicity and consistency, let's just reuse the logic from _format_account_async
        # which fetches fresh prices for all positions. This is slightly inefficient (fetching same symbol twice),
        # but ensures total equity is accurate across portfolio.
        
        # However, _format_account_async is async and we need to await it.
        # Also, we might want to avoid extra API calls.
        # But `account_final.positions` includes other symbols too.

        # Since we just executed a trade, returning the updated account via _format_account_async is the best way.

        formatted_account = await self._format_account_async(account_final)

        # We still need to construct the trade dict to return along with account
        trade_dict = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "price": current_price,
            "value": order_value,
            "timestamp": timestamp
        }

        return {
            "success": True,
            "trade": trade_dict,
            "account": formatted_account
        }
    
    async def get_paper_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all paper trading positions."""
        account_dict = await self.get_paper_account(user_id)
        if not account_dict:
            return []
        positions = account_dict.get('positions', {})

        return [
            {"symbol": symbol, **details}
            for symbol, details in positions.items()
        ]
    
    async def get_paper_trade_history(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get paper trading trade history."""
        # Get account ID first
        result = await self.session.execute(
            select(PaperAccount.id).where(PaperAccount.user_id == user_id)
        )
        account_id = result.scalar_one_or_none()

        if not account_id:
            return []

        trades_result = await self.session.execute(
            select(PaperTrade)
            .where(PaperTrade.account_id == account_id)
            .order_by(PaperTrade.timestamp.desc())
            .limit(limit)
        )

        trades = trades_result.scalars().all()

        # Convert to dict and reverse for chronological order
        trades_list = [
            {
                "symbol": t.symbol,
                "qty": t.qty,
                "side": t.side,
                "price": t.price,
                "value": t.value,
                "timestamp": t.timestamp
            }
            for t in reversed(trades)
        ]

        return trades_list


def get_paper_trading_service(session: AsyncSession) -> PaperTradingService:
    """
    Get paper trading service instance.

    Args:
        session: AsyncSession - Database session (required)

    Returns:
        PaperTradingService instance
    """
    return PaperTradingService(session)
