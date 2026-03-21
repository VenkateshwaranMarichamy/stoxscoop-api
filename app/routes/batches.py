from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.batches import BatchCreate, BatchRead, BatchWithEventsCreate, BatchWithEventsRead
from app.services.batches import create_batch, create_batch_with_events, list_batches


router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchRead, status_code=201)
def create(payload: BatchCreate, db: Session = Depends(get_db)) -> BatchRead:
    return create_batch(db, payload)


@router.post("/with-events", response_model=BatchWithEventsRead, status_code=201)
def create_with_events(payload: BatchWithEventsCreate, db: Session = Depends(get_db)) -> BatchWithEventsRead:
    batch, events = create_batch_with_events(db, payload)
    return {"batch": batch, "events": events}


@router.get("", response_model=list[BatchRead])
def list_(  # noqa: ANN201
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_batches(db, limit=limit, offset=offset)

