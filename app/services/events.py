from __future__ import annotations

from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import NotFoundError
from app.models.event_batches import EventBatch
from app.models.event_details import (
    AcquisitionDetails,
    AuditorResignationDetails,
    BoardChangeDetails,
    BuybackDetails,
    ContractDetails,
    CreditRatingDetails,
    FiiDiiDetails,
    InsiderTradingDetails,
    MutualFundDetails,
    PledgeDetails,
    SebiActionDetails,
    StakeTransactionDetails,
)
from app.models.events import Event
from app.models.stocks import Stock
from app.schemas.events import EventCreate


DETAIL_MODEL_BY_FIELD = {
    "stake_transaction_details": StakeTransactionDetails,
    "contract_details": ContractDetails,
    "buyback_details": BuybackDetails,
    "acquisition_details": AcquisitionDetails,
    "pledge_details": PledgeDetails,
    "insider_trading_details": InsiderTradingDetails,
    "sebi_action_details": SebiActionDetails,
    "fii_dii_details": FiiDiiDetails,
    "mutual_fund_details": MutualFundDetails,
    "credit_rating_details": CreditRatingDetails,
    "auditor_resignation_details": AuditorResignationDetails,
    "board_change_details": BoardChangeDetails,
}


def _assert_stocks_exist(db: Session, stock_ids: set[int]) -> None:
    if not stock_ids:
        return
    found = set(db.execute(select(Stock.id).where(Stock.id.in_(stock_ids))).scalars().all())
    missing = stock_ids - found
    if missing:
        raise NotFoundError(f"Unknown stock_id(s): {sorted(missing)}")


def _assert_batches_exist(db: Session, batch_ids: set[int]) -> None:
    if not batch_ids:
        return
    found = set(db.execute(select(EventBatch.id).where(EventBatch.id.in_(batch_ids))).scalars().all())
    missing = batch_ids - found
    if missing:
        raise NotFoundError(f"Unknown batch_id(s): {sorted(missing)}")


def _build_event_and_detail(payload: EventCreate) -> tuple[Event, object | None]:
    event = Event(
        stock_id=payload.stock_id,
        batch_id=payload.batch_id,
        event_type=payload.event_type,
        title=payload.title,
        event_date=payload.event_date,
        priority=payload.priority,
        impact_score=payload.impact_score,
        source_url=str(payload.source_url) if payload.source_url is not None else None,
    )

    detail_obj: object | None = None
    for field, model in DETAIL_MODEL_BY_FIELD.items():
        details = getattr(payload, field)
        if details is not None:
            detail_obj = model(**details.model_dump())
            break
    return event, detail_obj


def create_event(db: Session, payload: EventCreate) -> Event:
    _assert_stocks_exist(db, {payload.stock_id})
    _assert_batches_exist(db, {payload.batch_id} if payload.batch_id is not None else set())

    event, detail = _build_event_and_detail(payload)
    db.add(event)
    db.flush()  # assigns event.id
    if detail is not None:
        detail.event_id = event.id  # type: ignore[attr-defined]
        db.add(detail)
    db.commit()
    db.refresh(event)
    return get_event(db, event.id)


def create_events_bulk(db: Session, payloads: list[EventCreate]) -> list[Event]:
    stock_ids = {p.stock_id for p in payloads}
    batch_ids = {p.batch_id for p in payloads if p.batch_id is not None}
    _assert_stocks_exist(db, stock_ids)
    _assert_batches_exist(db, batch_ids)

    events: list[Event] = []
    details_by_index: list[object | None] = []

    for p in payloads:
        event, detail = _build_event_and_detail(p)
        events.append(event)
        details_by_index.append(detail)

    db.add_all(events)
    db.flush()

    for ev, detail in zip(events, details_by_index, strict=True):
        if detail is not None:
            detail.event_id = ev.id  # type: ignore[attr-defined]
            db.add(detail)

    db.commit()
    ids = [e.id for e in events]
    return list_events_by_ids(db, ids)


def list_events_by_ids(db: Session, ids: list[int]) -> list[Event]:
    if not ids:
        return []
    stmt = (
        select(Event)
        .where(Event.id.in_(ids))
        .options(
            joinedload(Event.stake_transaction_details),
            joinedload(Event.contract_details),
            joinedload(Event.buyback_details),
            joinedload(Event.acquisition_details),
            joinedload(Event.pledge_details),
            joinedload(Event.insider_trading_details),
            joinedload(Event.sebi_action_details),
            joinedload(Event.fii_dii_details),
            joinedload(Event.mutual_fund_details),
            joinedload(Event.credit_rating_details),
            joinedload(Event.auditor_resignation_details),
            joinedload(Event.board_change_details),
        )
    )
    by_id = {e.id: e for e in db.execute(stmt).scalars().all()}
    return [by_id[i] for i in ids if i in by_id]


def get_event(db: Session, event_id: int) -> Event:
    stmt = (
        select(Event)
        .where(Event.id == event_id)
        .options(
            joinedload(Event.stake_transaction_details),
            joinedload(Event.contract_details),
            joinedload(Event.buyback_details),
            joinedload(Event.acquisition_details),
            joinedload(Event.pledge_details),
            joinedload(Event.insider_trading_details),
            joinedload(Event.sebi_action_details),
            joinedload(Event.fii_dii_details),
            joinedload(Event.mutual_fund_details),
            joinedload(Event.credit_rating_details),
            joinedload(Event.auditor_resignation_details),
            joinedload(Event.board_change_details),
        )
    )
    event = db.execute(stmt).scalars().first()
    if event is None:
        raise NotFoundError("Event not found")
    return event


def list_events(
    db: Session,
    *,
    stock_id: int | None = None,
    symbol: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    event_type: str | None = None,
    priority: str | None = None,
    impact_score_min: int | None = None,
    impact_score_max: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Event]:
    filters: list[object] = []
    stmt = select(Event)

    if symbol is not None:
        stmt = stmt.join(Stock, Stock.id == Event.stock_id)
        filters.append(Stock.symbol == symbol)
    if stock_id is not None:
        filters.append(Event.stock_id == stock_id)
    if date_from is not None:
        filters.append(Event.event_date >= date_from)
    if date_to is not None:
        filters.append(Event.event_date <= date_to)
    if event_type is not None:
        filters.append(Event.event_type == event_type)
    if priority is not None:
        filters.append(Event.priority == priority)
    if impact_score_min is not None:
        filters.append(Event.impact_score >= impact_score_min)
    if impact_score_max is not None:
        filters.append(Event.impact_score <= impact_score_max)

    if filters:
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(Event.event_date.desc(), Event.id.desc()).limit(limit).offset(offset)
    stmt = stmt.options(
        joinedload(Event.stake_transaction_details),
        joinedload(Event.contract_details),
        joinedload(Event.buyback_details),
        joinedload(Event.acquisition_details),
        joinedload(Event.pledge_details),
        joinedload(Event.insider_trading_details),
        joinedload(Event.sebi_action_details),
        joinedload(Event.fii_dii_details),
        joinedload(Event.mutual_fund_details),
        joinedload(Event.credit_rating_details),
        joinedload(Event.auditor_resignation_details),
        joinedload(Event.board_change_details),
    )
    return list(db.execute(stmt).scalars().all())

