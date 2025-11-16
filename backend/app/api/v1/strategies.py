"""
Strategies API routes.
Handles strategy CRUD operations, ticker management, and backtesting.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.strategy import Strategy, StrategyTicker
from app.schemas.strategy import (
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyTickerCreate,
    StrategyTickerResponse,
)
from app.dependencies import get_current_active_user


router = APIRouter()


@router.get("", response_model=List[StrategyResponse])
async def list_strategies(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all strategies for current user.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    result = await db.execute(
        select(Strategy)
        .where(Strategy.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(Strategy.created_at.desc())
    )
    strategies = result.scalars().all()
    
    return strategies


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    print(f"\n--- Debug: create_strategy endpoint START ---")
    print(f"create_strategy: db object at start: {db}")
    print(f"create_strategy: type of db at start: {type(db)}")
    print(f"create_strategy: current_user.id: {current_user.id}")
    print(f"create_strategy: strategy_data: {strategy_data.dict()}")

    # Create strategy
    new_strategy = Strategy(
        user_id=current_user.id,
        name=strategy_data.name,
        description=strategy_data.description,
        strategy_type=strategy_data.strategy_type,
        parameters=strategy_data.parameters,
    )
    print(f"create_strategy: New strategy object created: {new_strategy}")
    
    print(f"create_strategy: Adding new_strategy to db session.")
    db.add(new_strategy)
    print(f"create_strategy: Calling db.commit() (mocked to flush).")
    await db.commit() # This is now db.flush() in tests
    print(f"create_strategy: db.commit() (flush) completed.")
    print(f"create_strategy: Calling db.refresh(new_strategy).")
    await db.refresh(new_strategy)
    print(f"create_strategy: db.refresh(new_strategy) completed. new_strategy ID: {new_strategy.id}")
    print(f"create_strategy: db object after refresh: {db}")
    print(f"create_strategy: type of db after refresh: {type(db)}")
    print(f"create_strategy: Calling db.expire(new_strategy).")
    await db.expire(new_strategy) # <--- Error occurs here
    print(f"create_strategy: db.expire(new_strategy) called successfully.")
    
    # Add tickers if provided
    if strategy_data.tickers:
        print(f"create_strategy: Tickers provided: {strategy_data.tickers}")
        for ticker in strategy_data.tickers:
            strategy_ticker = StrategyTicker(
                strategy_id=new_strategy.id,
                ticker=ticker,
            )
            print(f"create_strategy: Adding strategy_ticker: {strategy_ticker.ticker}")
            db.add(strategy_ticker)
        
        print(f"create_strategy: Calling db.commit() (mocked to flush) for tickers.")
        await db.commit()
        print(f"create_strategy: db.commit() (flush) for tickers completed.")
        print(f"create_strategy: db object after ticker commit: {db}")
        print(f"create_strategy: type of db after ticker commit: {type(db)}")
        print(f"create_strategy: Calling db.expire(new_strategy) after ticker commit.")
        await db.expire(new_strategy) # Also expire after ticker commit
        print(f"create_strategy: db.expire(new_strategy) after ticker commit called successfully.")
    
    print(f"create_strategy: Returning new_strategy: {new_strategy.id}")
    print(f"--- Debug: create_strategy endpoint END ---")
    return new_strategy


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific strategy by ID.
    """
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: str,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a strategy.
    
    - **name**: Update strategy name
    - **description**: Update description
    - **parameters**: Update strategy parameters
    - **is_active**: Enable/disable strategy
    """
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Update fields if provided
    if strategy_update.name is not None:
        strategy.name = strategy_update.name
    
    if strategy_update.description is not None:
        strategy.description = strategy_update.description
    
    if strategy_update.parameters is not None:
        strategy.parameters = strategy_update.parameters
    
    if strategy_update.is_active is not None:
        strategy.is_active = strategy_update.is_active
    
    await db.commit()
    await db.refresh(strategy)
    
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a strategy.
    
    This will also delete all associated tickers and trades.
    """
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    await db.delete(strategy)
    await db.commit()
    
    return None


@router.get("/{strategy_id}/tickers", response_model=List[StrategyTickerResponse])
async def list_strategy_tickers(
    strategy_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all tickers associated with a strategy.
    """
    # Verify strategy ownership
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get tickers
    result = await db.execute(
        select(StrategyTicker).where(StrategyTicker.strategy_id == strategy_id)
    )
    tickers = result.scalars().all()
    
    return tickers


@router.post("/{strategy_id}/tickers", response_model=StrategyTickerResponse, status_code=status.HTTP_201_CREATED)
async def add_strategy_ticker(
    strategy_id: str,
    ticker_data: StrategyTickerCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a ticker to a strategy.
    """
    # Verify strategy ownership
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Check if ticker already exists for this strategy
    result = await db.execute(
        select(StrategyTicker).where(
            StrategyTicker.strategy_id == strategy_id,
            StrategyTicker.ticker == ticker_data.ticker
        )
    )
    existing_ticker = result.scalar_one_or_none()
    
    if existing_ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker already added to this strategy"
        )
    
    # Create ticker
    new_ticker = StrategyTicker(
        strategy_id=strategy_id,
        ticker=ticker_data.ticker,
        allocation_percent=ticker_data.allocation_percent,
    )
    
    db.add(new_ticker)
    await db.commit()
    await db.refresh(new_ticker)
    
    return new_ticker


@router.delete("/{strategy_id}/tickers/{ticker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_strategy_ticker(
    strategy_id: str,
    ticker_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a ticker from a strategy.
    """
    # Verify strategy ownership
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.user_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found"
        )
    
    # Get ticker
    result = await db.execute(
        select(StrategyTicker).where(
            StrategyTicker.id == ticker_id,
            StrategyTicker.strategy_id == strategy_id
        )
    )
    ticker = result.scalar_one_or_none()
    
    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticker not found"
        )
    
    await db.delete(ticker)
    await db.commit()
    
    return None
