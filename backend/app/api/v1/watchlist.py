"""
Watchlist management API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
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
    # TODO: Implement after models are deployed
    # from app.models.watchlist import Watchlist
    # query = select(Watchlist).where(Watchlist.user_id == current_user.id)
    # result = await db.execute(query)
    # watchlists = result.scalars().all()
    
    # Placeholder response
    return {
        "total_watchlists": 0,
        "total_symbols": 0,
        "watchlists": []
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
    # TODO: Implement after models are deployed
    # from app.models.watchlist import Watchlist
    # new_watchlist = Watchlist(
    #     user_id=current_user.id,
    #     name=watchlist_data.name,
    #     description=watchlist_data.description
    # )
    # db.add(new_watchlist)
    # await db.commit()
    # await db.refresh(new_watchlist)
    # return new_watchlist
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed. See implementation_plan.md"
    )


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
async def get_watchlist(
    watchlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific watchlist by ID with real-time prices.
    """
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )


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
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a watchlist and all its items.
    """
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )


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
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
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
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )


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
    # TODO: Implement after models are deployed
    return []


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
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )


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
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_price_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a price alert.
    """
    # TODO: Implement after models are deployed
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Watchlist models need to be deployed"
    )
