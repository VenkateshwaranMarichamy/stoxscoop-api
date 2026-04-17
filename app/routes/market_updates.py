from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.market_updates import MarketUpdateCreate, MarketUpdateRead, MarketUpdateUpdate
from app.services import market_updates as service


router = APIRouter(prefix="/api/v1/market-updates", tags=["market-updates"])


@router.post("", response_model=MarketUpdateRead, status_code=201)
def create_market_update(payload: MarketUpdateCreate, db: Session = Depends(get_db)) -> MarketUpdateRead:
    return service.create_market_update(db, payload)


@router.get("", response_model=list[MarketUpdateRead])
def list_market_updates(
    category: str | None = None,
    sentiment: str | None = None,
    impact: str | None = None,
    date_from: datetime | None = Query(None, description="Filter by published_at >= date_from"),
    date_to: datetime | None = Query(None, description="Filter by published_at <= date_to"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[MarketUpdateRead]:
    return service.list_market_updates(
        db,
        category=category,
        sentiment=sentiment,
        impact=impact,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/{update_id}", response_model=MarketUpdateRead)
def get_market_update(update_id: int, db: Session = Depends(get_db)) -> MarketUpdateRead:
    return service.get_market_update(db, update_id)


@router.patch("/{update_id}", response_model=MarketUpdateRead)
def update_market_update(
    update_id: int,
    payload: MarketUpdateUpdate,
    db: Session = Depends(get_db),
) -> MarketUpdateRead:
    return service.update_market_update(db, update_id, payload)
