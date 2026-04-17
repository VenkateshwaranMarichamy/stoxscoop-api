from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

import logging

from app.core.errors import BadRequestError, NotFoundError
from app.models.v1 import (
    BusinessEventDetails,
    CorporateActionDetails,
    StoxCreditRatingDetails,
    DisclosureDetails,
    EventSubtype,
    FinancialResultDetails,
    FundraisingDetails,
    GovernanceDetails,
    InsiderDetails,
    IngestionSourceEnum,
    LegalDetails,
    PriorityEnum,
    SentimentEnum,
    StoxEvent,
    StoxEventBatch,
)
from app.schemas.v1 import BatchCreate, BatchWithEventsCreate, EventCreate, EventUpdate, BatchWithEventsPartialRead


DETAIL_MODEL_BY_EVENT_TYPE = {
    "corporate_action": CorporateActionDetails,
    "disclosure": DisclosureDetails,
    "insider": InsiderDetails,
    "business": BusinessEventDetails,
    "governance": GovernanceDetails,
    "credit_rating": StoxCreditRatingDetails,
    "financials": FinancialResultDetails,
    "fundraising": FundraisingDetails,
    "legal": LegalDetails,
}

# Columns backed by PostgreSQL ENUMs in stoxscoop (see stocsccoop-backend-22ndMar.sql).
# UI may send UPPERCASE; we persist lowercase labels the DB expects.
DETAIL_PG_ENUM_STRING_COLUMNS: dict[type, frozenset[str]] = {
    DisclosureDetails: frozenset({"investor_category", "transaction_type", "transaction_mode"}),
    InsiderDetails: frozenset({"transaction_type"}),
    BusinessEventDetails: frozenset({"contract_type"}),
    StoxCreditRatingDetails: frozenset({"agency"}),
    FinancialResultDetails: frozenset({"beat_miss"}),
    LegalDetails: frozenset({"outcome"}),
}


def _normalize_detail_payload_for_pg(model: type, payload: dict[str, Any]) -> dict[str, Any]:
    keys = DETAIL_PG_ENUM_STRING_COLUMNS.get(model)
    if not keys:
        return payload
    out = dict(payload)
    for k in keys:
        val = out.get(k)
        if val is not None and isinstance(val, str):
            out[k] = val.strip().lower()
    return out


def _ensure_stock_exists(db: Session, stock_id: int) -> None:
    exists = db.execute(
        text("SELECT 1 FROM classification.ticker_symbol WHERE id = :id LIMIT 1"),
        {"id": stock_id},
    ).first()
    if exists is None:
        raise NotFoundError(f"Unknown stock_id: {stock_id}")


def _ensure_batch_exists(db: Session, batch_id: int) -> None:
    exists = db.execute(select(StoxEventBatch.id).where(StoxEventBatch.id == batch_id)).scalar_one_or_none()
    if exists is None:
        raise NotFoundError(f"Unknown batch_id: {batch_id}")


def _get_subtype(db: Session, event_type: str, event_subtype: str) -> EventSubtype:
    subtype = db.execute(
        select(EventSubtype).where(
            EventSubtype.event_type == event_type,
            EventSubtype.subtype_code == event_subtype,
        )
    ).scalar_one_or_none()
    if subtype is None:
        raise BadRequestError(f"Invalid event_type/event_subtype pair: {event_type}/{event_subtype}")
    return subtype


def _model_to_dict(model_obj: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for col in model_obj.__table__.columns:
        if col.name in {"id", "event_id"}:
            continue
        data[col.name] = getattr(model_obj, col.name)
    return data


def _coerce_empty_strings(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert empty string values to None to avoid type errors on numeric/date DB columns."""
    return {k: (None if v == "" else v) for k, v in payload.items()}


def _upsert_detail(db: Session, event: StoxEvent, detail_payload: dict[str, Any] | None) -> None:
    if not detail_payload:
        return
    model = DETAIL_MODEL_BY_EVENT_TYPE[event.event_type.value]
    cols = {c.name for c in model.__table__.columns} - {"id", "event_id"}
    clean_payload = {k: v for k, v in detail_payload.items() if k in cols}
    clean_payload = _coerce_empty_strings(clean_payload)
    clean_payload = _normalize_detail_payload_for_pg(model, clean_payload)
    existing = db.execute(select(model).where(model.event_id == event.id)).scalar_one_or_none()
    if existing is None:
        db.add(model(event_id=event.id, **clean_payload))
        return
    for k, v in clean_payload.items():
        setattr(existing, k, v)


def _event_with_detail_dict(db: Session, event: StoxEvent) -> dict[str, Any]:
    model = DETAIL_MODEL_BY_EVENT_TYPE[event.event_type.value]
    detail = db.execute(select(model).where(model.event_id == event.id)).scalar_one_or_none()
    base = {
        "id": event.id,
        "stock_id": event.stock_id,
        "batch_id": event.batch_id,
        "event_type": event.event_type,
        "event_subtype": event.event_subtype,
        "signal_type": event.signal_type,
        "signal_reason": event.signal_reason,
        "sentiment": event.sentiment,
        "priority": event.priority,
        "impact_score": event.impact_score,
        "confidence_score": float(event.confidence_score) if event.confidence_score is not None else None,
        "confidence_model_version": event.confidence_model_version,
        "tags": event.tags,
        "title": event.title,
        "summary": event.summary,
        "event_date": event.event_date,
        "source_url": event.source_url,
        "source_name": event.source_name,
        "ingestion_source": event.ingestion_source,
        "is_verified": event.is_verified,
        "is_active": event.is_active,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
        "detail": _model_to_dict(detail) if detail else None,
    }
    return base


def create_batch(db: Session, payload: BatchCreate) -> StoxEventBatch:
    batch = StoxEventBatch(batch_name=payload.batch_name, notes=payload.notes, ingestion_source=IngestionSourceEnum.manual)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def list_batches(db: Session, limit: int, offset: int) -> list[StoxEventBatch]:
    return list(
        db.execute(select(StoxEventBatch).order_by(StoxEventBatch.started_at.desc()).limit(limit).offset(offset)).scalars().all()
    )


def complete_batch(db: Session, batch_id: int) -> StoxEventBatch:
    batch = db.get(StoxEventBatch, batch_id)
    if batch is None:
        raise NotFoundError("Batch not found")
    batch.completed_at = func.now()
    db.commit()
    db.refresh(batch)
    return batch


def get_batch(db: Session, batch_id: int) -> StoxEventBatch:
    batch = db.get(StoxEventBatch, batch_id)
    if batch is None:
        raise NotFoundError("Batch not found")
    return batch


def create_event(db: Session, payload: EventCreate) -> dict[str, Any]:
    _ensure_stock_exists(db, payload.stock_id)
    if payload.batch_id is not None:
        _ensure_batch_exists(db, payload.batch_id)
    subtype = _get_subtype(db, payload.event_type.value, payload.event_subtype)

    try:
        event = StoxEvent(
            stock_id=payload.stock_id,
            batch_id=payload.batch_id,
            event_type=payload.event_type,
            event_subtype=payload.event_subtype,
            signal_type=payload.signal_type or subtype.default_signal,
            signal_reason=payload.signal_reason,
            sentiment=payload.sentiment or SentimentEnum.neutral,
            priority=payload.priority or PriorityEnum.low,
            impact_score=payload.impact_score,
            tags=payload.tags or [],
            title=payload.title,
            summary=payload.summary,
            event_date=payload.event_date,
            source_url=payload.source_url,
            source_name=payload.source_name,
            ingestion_source=IngestionSourceEnum.manual,
            is_verified=True,
            is_active=True,
        )
        db.add(event)
        db.flush()
        _upsert_detail(db, event, payload.detail)
        if event.batch_id is not None:
            batch = db.get(StoxEventBatch, event.batch_id)
            if batch is not None:
                batch.total_events = (batch.total_events or 0) + 1
        db.commit()
        db.refresh(event)
        return _event_with_detail_dict(db, event)
    except Exception:
        db.rollback()
        raise


def create_events_batch(db: Session, batch_id: int | None, payloads: list[EventCreate]) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    if batch_id is not None:
        _ensure_batch_exists(db, batch_id)
    for p in payloads:
        item = p.model_copy(update={"batch_id": batch_id if batch_id is not None else p.batch_id})
        created.append(create_event(db, item))
    return created


def _sanitize_error_message(exc: Exception) -> str:
    """Remove SQL queries, table names, and stack traces from error messages."""
    error_msg = exc.message if hasattr(exc, "message") else str(exc)
    
    # Remove SQL query blocks
    if "SQL:" in error_msg or "[SQL:" in error_msg:
        error_msg = error_msg.split("SQL:")[0].split("[SQL:")[0].strip()
    
    # Remove background error URLs
    if "[Background on this error at:" in error_msg:
        error_msg = error_msg.split("[Background")[0].strip()
    
    # Remove psycopg2 error prefixes with table names
    if "(psycopg2.errors." in error_msg:
        parts = error_msg.split("** ")
        if len(parts) > 1:
            error_msg = parts[1].strip()
        else:
            error_msg = error_msg.split(") ")[-1].strip()
    
    # Remove trailing parentheses and brackets
    error_msg = error_msg.rstrip(")")
    
    return error_msg or "Validation failed"


def create_batch_with_events(db: Session, payload: BatchWithEventsCreate) -> dict[str, Any]:
    if not payload.events:
        raise BadRequestError("events must not be empty")
    batch = create_batch(db, BatchCreate(batch_name=payload.batch_name, notes=payload.notes))

    results: list[dict[str, Any]] = []
    created_count = 0
    failed_count = 0

    for i, event_payload in enumerate(payload.events):
        try:
            event_payload_with_batch = event_payload.model_copy(update={"batch_id": batch.id})
            event = create_event(db, event_payload_with_batch)
            results.append({"index": i, "status": "created", "id": event["id"], "error": None})
            created_count += 1
        except Exception as exc:
            failed_count += 1
            error_msg = _sanitize_error_message(exc)
            logging.getLogger("app").debug("Batch event index %d failed: %s", i, error_msg)
            results.append({"index": i, "status": "failed", "id": None, "error": error_msg})

    return {
        "batch": batch,
        "created": created_count,
        "failed": failed_count,
        "results": results,
    }


def list_events(
    db: Session,
    *,
    stock_id: int | None,
    event_type: str | None,
    event_subtype: str | None,
    date_from: date | None = None,
    date_to: date | None = None,
    priority: str | None = None,
    limit: int,
    offset: int,
    active_only: bool,
) -> list[dict[str, Any]]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise BadRequestError("date_from must be on or before date_to")

    stmt = select(StoxEvent).order_by(StoxEvent.event_date.desc(), StoxEvent.id.desc()).limit(limit).offset(offset)
    if stock_id is not None:
        stmt = stmt.where(StoxEvent.stock_id == stock_id)
    if event_type is not None:
        stmt = stmt.where(StoxEvent.event_type == event_type)
    if event_subtype is not None:
        stmt = stmt.where(StoxEvent.event_subtype == event_subtype.strip().lower())
    if date_from is not None:
        stmt = stmt.where(StoxEvent.event_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(StoxEvent.event_date <= date_to)
    if priority is not None:
        p = priority.strip().lower()
        try:
            priority_enum = PriorityEnum(p)
        except ValueError as err:
            raise BadRequestError(f"Invalid priority: {priority!r} (use low, medium, or high)") from err
        stmt = stmt.where(StoxEvent.priority == priority_enum)
    if active_only:
        stmt = stmt.where(StoxEvent.is_active.is_(True))
    events = db.execute(stmt).scalars().all()
    return [_event_with_detail_dict(db, e) for e in events]


def get_event(db: Session, event_id: int) -> dict[str, Any]:
    event = db.get(StoxEvent, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    return _event_with_detail_dict(db, event)


def update_event(db: Session, event_id: int, payload: EventUpdate) -> dict[str, Any]:
    event = db.get(StoxEvent, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    data = payload.model_dump(exclude_unset=True)
    detail = data.pop("detail", None)
    for k, v in data.items():
        setattr(event, k, v)
    if detail is not None:
        _upsert_detail(db, event, detail)
    db.commit()
    db.refresh(event)
    return _event_with_detail_dict(db, event)


def soft_delete_event(db: Session, event_id: int) -> None:
    event = db.get(StoxEvent, event_id)
    if event is None:
        raise NotFoundError("Event not found")
    event.is_active = False
    db.commit()


def list_subtypes(db: Session, event_type: str | None) -> list[EventSubtype]:
    stmt = select(EventSubtype).order_by(EventSubtype.event_type.asc(), EventSubtype.subtype_code.asc())
    if event_type is not None:
        stmt = stmt.where(EventSubtype.event_type == event_type)
    return list(db.execute(stmt).scalars().all())

