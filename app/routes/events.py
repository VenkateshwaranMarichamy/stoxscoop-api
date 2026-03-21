from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import EventType, Priority
from app.schemas.events import EventCreate, EventRead
from app.services.events import create_event, create_events_bulk, get_event, list_events


router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=201)
def create(payload: EventCreate, db: Session = Depends(get_db)) -> EventRead:
    return create_event(db, payload)


@router.post("/batch", response_model=list[EventRead], status_code=201)
def create_batch(payload: list[EventCreate], db: Session = Depends(get_db)) -> list[EventRead]:
    return create_events_bulk(db, payload)


@router.get("", response_model=list[EventRead])
def list_(  # noqa: ANN201
    stock_id: int | None = Query(default=None, ge=1),
    symbol: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: EventType | None = None,
    priority: Priority | None = None,
    impact_score_min: int | None = Query(default=None, ge=1, le=10),
    impact_score_max: int | None = Query(default=None, ge=1, le=10),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_events(
        db,
        stock_id=stock_id,
        symbol=symbol,
        date_from=date_from,
        date_to=date_to,
        event_type=event_type.value if event_type is not None else None,
        priority=priority.value if priority is not None else None,
        impact_score_min=impact_score_min,
        impact_score_max=impact_score_max,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=EventRead)
def get(event_id: int, db: Session = Depends(get_db)) -> EventRead:
    return get_event(db, event_id)

