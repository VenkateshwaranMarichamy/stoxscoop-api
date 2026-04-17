from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.v1 import EventTypeEnum
from app.schemas.v1 import (
    BatchCreate,
    BatchRead,
    BatchWithEventsCreate,
    BatchWithEventsPartialRead,
    BatchWithEventsRead,
    EventBatchCreate,
    EventCreate,
    EventRead,
    EventUpdate,
    SubtypeRead,
)
from app.services import v1 as service


router = APIRouter(prefix="/api/v1", tags=["v1"])


@router.post("/batches", response_model=BatchRead, status_code=201)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db)) -> BatchRead:
    return service.create_batch(db, payload)


@router.get("/batches", response_model=list[BatchRead])
def list_batches(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[BatchRead]:
    return service.list_batches(db, limit, offset)


@router.get("/batches/{batch_id}", response_model=BatchWithEventsRead)
def get_batch(batch_id: int, db: Session = Depends(get_db)) -> BatchWithEventsRead:
    batch = service.get_batch(db, batch_id)
    events = service.list_events(
        db,
        stock_id=None,
        event_type=None,
        event_subtype=None,
        date_from=None,
        date_to=None,
        priority=None,
        limit=10000,
        offset=0,
        active_only=False,
    )
    events = [e for e in events if e["batch_id"] == batch_id]
    return {"batch": batch, "events": events}


@router.patch("/batches/{batch_id}/complete", response_model=BatchRead)
def complete_batch(batch_id: int, db: Session = Depends(get_db)) -> BatchRead:
    return service.complete_batch(db, batch_id)


@router.post("/batches/with-events", response_model=BatchWithEventsPartialRead, status_code=201)
def create_batch_with_events(payload: BatchWithEventsCreate, db: Session = Depends(get_db)) -> BatchWithEventsPartialRead:
    return service.create_batch_with_events(db, payload)


@router.post("/events", response_model=EventRead, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventRead:
    return service.create_event(db, payload)


@router.post("/events/batch", response_model=list[EventRead], status_code=201)
def create_events_batch(payload: EventBatchCreate, db: Session = Depends(get_db)) -> list[EventRead]:
    return service.create_events_batch(db, payload.batch_id, payload.events)


@router.get("/events", response_model=list[EventRead])
def list_events(
    stock_id: int | None = None,
    event_type: EventTypeEnum | None = None,
    event_subtype: str | None = None,
    date_from: date | None = Query(
        None,
        description="Include events with event_date on or after this date (inclusive).",
    ),
    date_to: date | None = Query(
        None,
        description="Include events with event_date on or before this date (inclusive).",
    ),
    priority: str | None = Query(
        None,
        description="Filter by priority: low, medium, or high (case-insensitive).",
    ),
    active_only: bool = True,
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[EventRead]:
    return service.list_events(
        db,
        stock_id=stock_id,
        event_type=event_type.value if event_type else None,
        event_subtype=event_subtype,
        date_from=date_from,
        date_to=date_to,
        priority=priority,
        limit=limit,
        offset=offset,
        active_only=active_only,
    )


@router.get("/events/{event_id}", response_model=EventRead)
def get_event(event_id: int, db: Session = Depends(get_db)) -> EventRead:
    return service.get_event(db, event_id)


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)) -> EventRead:
    return service.update_event(db, event_id, payload)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> Response:
    service.soft_delete_event(db, event_id)
    return Response(status_code=204)


@router.get("/subtypes", response_model=list[SubtypeRead])
def list_subtypes(event_type: EventTypeEnum | None = None, db: Session = Depends(get_db)) -> list[SubtypeRead]:
    return service.list_subtypes(db, event_type.value if event_type else None)

