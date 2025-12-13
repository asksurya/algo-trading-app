"""
Watchlist management API endpoints.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem, PriceAlert
from app.schemas.watchlist import (
    WatchlistCreate,
    WatchlistUpdate,
    WatchlistResponse,
    WatchlistItemCreate,
    WatchlistItemResponse,
    PriceAlertCreate,
    PriceAlertUpdate,
    PriceAlertResponse,
    WatchlistSummaryResponse
)

router = APIRouter()


# Watchlist CRUD


@router.get("", response_model=WatchlistSummaryResponse)
async def list_watchlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all watchlists for the current user.
    """
    query = select(Watchlist).where(Watchlist.user_id == current_user.id).options(selectinload(Watchlist.items))
    result = await db.execute(query)
    watchlists = result.scalars().all()

    total_watchlists = len(watchlists)
    total_symbols = sum(len(wl.items) for wl in watchlists)
    
    return {
        "total_watchlists": total_watchlists,
        "total_symbols": total_symbols,
        "watchlists": watchlists
    }


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new watchlist.
    """
    new_watchlist = Watchlist(
        user_id=current_user.id,
        name=watchlist_data.name,
        description=watchlist_data.description
    )
    db.add(new_watchlist)
    await db.commit()
    await db.refresh(new_watchlist)

    # We need to refresh items too (empty list initially)
    # But loading it explicitly might be safer to match response model expectation
    await db.refresh(new_watchlist, attribute_names=["items"])

    return new_watchlist


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific watchlist by ID with real-time prices.
    """
    query = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).options(selectinload(Watchlist.items))

    result = await db.execute(query)
    watchlist = result.scalars().first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )

    # TODO: Fetch real-time prices for items and populate response
    # This part would typically involve calling a market data service
    # For now, we return the watchlist with items without real-time data

    return watchlist


@router.put("/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist(
    watchlist_id: str,
    watchlist_update: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update watchlist name or description.
    """
    query = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    ).options(selectinload(Watchlist.items))

    result = await db.execute(query)
    watchlist = result.scalars().first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )

    if watchlist_update.name is not None:
        watchlist.name = watchlist_update.name
    if watchlist_update.description is not None:
        watchlist.description = watchlist_update.description

    await db.commit()
    await db.refresh(watchlist)
    return watchlist


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a watchlist and all its items.
    """
    query = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    )
    result = await db.execute(query)
    watchlist = result.scalars().first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )

    await db.delete(watchlist)
    await db.commit()


# Watchlist Items


@router.post("/{watchlist_id}/items", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_watchlist(
    watchlist_id: str,
    item_data: WatchlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a symbol to a watchlist.
    """
    # Verify watchlist exists and belongs to user
    query = select(Watchlist).where(
        Watchlist.id == watchlist_id,
        Watchlist.user_id == current_user.id
    )
    result = await db.execute(query)
    watchlist = result.scalars().first()

    if not watchlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found"
        )

    # Check if item already exists
    query = select(WatchlistItem).where(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.symbol == item_data.symbol
    )
    result = await db.execute(query)
    existing_item = result.scalars().first()

    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Symbol {item_data.symbol} is already in the watchlist"
        )

    new_item = WatchlistItem(
        watchlist_id=watchlist_id,
        symbol=item_data.symbol,
        notes=item_data.notes
    )

    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)

    # The response model expects added_at which corresponds to created_at from TimestampMixin
    # We might need to map created_at to added_at or update the schema to use created_at
    # Looking at the schema, it expects 'added_at'. Since TimestampMixin provides 'created_at',
    # we can alias it in the response or just let Pydantic handle it if we alias the field in schema.
    # But schema defines added_at. Let's check WatchlistItem model again.
    # It inherits TimestampMixin which has created_at.
    # So we need to ensure the response model gets the right value.
    # We can handle this by constructing the response object manually or modifying schema.
    # For now, let's just return the object and hope Pydantic configuration handles alias or we might need a small fix.

    # Wait, WatchlistItemResponse defines added_at. WatchlistItem has created_at.
    # I should modify the return to map created_at to added_at explicitly.

    return WatchlistItemResponse(
        id=new_item.id,
        symbol=new_item.symbol,
        notes=new_item.notes,
        added_at=new_item.created_at
    )


@router.delete("/{watchlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_watchlist(
    watchlist_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a symbol from a watchlist.
    """
    # Verify watchlist exists and belongs to user
    # We can join to verify both at once
    query = select(WatchlistItem).join(Watchlist).where(
        WatchlistItem.id == item_id,
        WatchlistItem.watchlist_id == watchlist_id,
        Watchlist.user_id == current_user.id
    )
    result = await db.execute(query)
    item = result.scalars().first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found"
        )

    await db.delete(item)
    await db.commit()


# Price Alerts


@router.get("/alerts", response_model=List[PriceAlertResponse])
async def list_price_alerts(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all price alerts for the current user.
    
    **Query Parameters:**
    - `active_only`: If true, only return active (not triggered) alerts
    """
    query = select(PriceAlert).where(PriceAlert.user_id == current_user.id)

    if active_only:
        query = query.where(PriceAlert.is_active == True)

    result = await db.execute(query)
    alerts = result.scalars().all()
    return alerts


@router.post("/alerts", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_price_alert(
    alert_data: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new price alert.
    
    The alert will trigger when the symbol's price crosses the target price
    based on the specified condition ('above' or 'below').
    """
    new_alert = PriceAlert(
        user_id=current_user.id,
        symbol=alert_data.symbol,
        condition=alert_data.condition,
        target_price=alert_data.target_price,
        message=alert_data.message,
        is_active=True
    )

    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)
    return new_alert


@router.put("/alerts/{alert_id}", response_model=PriceAlertResponse)
async def update_price_alert(
    alert_id: str,
    alert_update: PriceAlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a price alert.
    """
    query = select(PriceAlert).where(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    )
    result = await db.execute(query)
    alert = result.scalars().first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price alert not found"
        )

    if alert_update.condition is not None:
        alert.condition = alert_update.condition
    if alert_update.target_price is not None:
        alert.target_price = alert_update.target_price
    if alert_update.message is not None:
        alert.message = alert_update.message
    if alert_update.is_active is not None:
        alert.is_active = alert_update.is_active

    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a price alert.
    """
    query = select(PriceAlert).where(
        PriceAlert.id == alert_id,
        PriceAlert.user_id == current_user.id
    )
    result = await db.execute(query)
    alert = result.scalars().first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price alert not found"
        )

    await db.delete(alert)
    await db.commit()
