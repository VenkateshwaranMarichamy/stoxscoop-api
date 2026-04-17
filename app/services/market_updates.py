from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.market_updates import MarketUpdate
from app.schemas.market_updates import MarketUpdateCreate, MarketUpdateUpdate


def create_market_update(db: Session, payload: MarketUpdateCreate) -> MarketUpdate:
    obj = MarketUpdate(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_market_update(db: Session, update_id: int) -> MarketUpdate:
    obj = db.get(MarketUpdate, update_id)
    if obj is None:
        raise NotFoundError("Market update not found")
    return obj


def list_market_updates(
    db: Session,
    *,
    category: str | None = None,
    sentiment: str | None = None,
    impact: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[MarketUpdate]:
    stmt = select(MarketUpdate).order_by(MarketUpdate.published_at.desc(), MarketUpdate.id.desc())
    if category is not None:
        stmt = stmt.where(MarketUpdate.category == category)
    if sentiment is not None:
        stmt = stmt.where(MarketUpdate.sentiment == sentiment.lower())
    if impact is not None:
        stmt = stmt.where(MarketUpdate.impact == impact.lower())
    if date_from is not None:
        stmt = stmt.where(MarketUpdate.published_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(MarketUpdate.published_at <= date_to)
    stmt = stmt.limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def update_market_update(db: Session, update_id: int, payload: MarketUpdateUpdate) -> MarketUpdate:
    obj = get_market_update(db, update_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
