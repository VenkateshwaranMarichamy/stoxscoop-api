from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError
from app.models.event_batches import EventBatch
from app.schemas.batches import BatchCreate, BatchWithEventsCreate
from app.services import events as events_service


def create_batch(db: Session, payload: BatchCreate) -> EventBatch:
    batch = EventBatch(batch_name=payload.batch_name, notes=payload.notes)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def list_batches(db: Session, limit: int = 50, offset: int = 0) -> list[EventBatch]:
    stmt = select(EventBatch).order_by(EventBatch.created_at.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def create_batch_with_events(db: Session, payload: BatchWithEventsCreate) -> tuple[EventBatch, list[events_service.Event]]:
    if not payload.events:
        raise BadRequestError("events must not be empty")

    stock_ids = {e.stock_id for e in payload.events}
    events_service._assert_stocks_exist(db, stock_ids)  # noqa: SLF001

    # NOTE: Don't use `with db.begin()` here because the Session may already
    # have an implicit transaction started by earlier SELECTs.
    try:
        batch = EventBatch(batch_name=payload.batch_name, notes=payload.notes)
        db.add(batch)
        db.flush()

        # Attach this batch_id to all events, then create them.
        events_payloads = [e.model_copy(update={"batch_id": batch.id}) for e in payload.events]

        events: list[events_service.Event] = []
        details_by_index: list[object | None] = []

        for p in events_payloads:
            ev, detail = events_service._build_event_and_detail(p)  # noqa: SLF001
            events.append(ev)
            details_by_index.append(detail)

        db.add_all(events)
        db.flush()

        for ev, detail in zip(events, details_by_index, strict=True):
            if detail is not None:
                detail.event_id = ev.id  # type: ignore[attr-defined]
                db.add(detail)

        ids = [e.id for e in events]
        created_events = events_service.list_events_by_ids(db, ids)

        db.commit()
        db.refresh(batch)
        return batch, created_events
    except Exception:
        db.rollback()
        raise

