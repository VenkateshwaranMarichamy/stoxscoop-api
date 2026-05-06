from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base

EVENTS_SCHEMA = settings.events_schema


def _events_enum(enum_cls: type[enum.Enum], pg_name: str) -> Enum:
    """Bind to enums that already exist under EVENTS_SCHEMA in PostgreSQL (no CREATE TYPE)."""

    return Enum(
        enum_cls,
        name=pg_name,
        schema=EVENTS_SCHEMA,
        values_callable=lambda e: [i.value for i in e],
        native_enum=True,
        create_type=False,
    )


class EventTypeEnum(str, enum.Enum):
    corporate_action = "corporate_action"
    disclosure = "disclosure"
    insider = "insider"
    business = "business"
    governance = "governance"
    credit_rating = "credit_rating"
    financials = "financials"
    fundraising = "fundraising"
    legal = "legal"


class SignalTypeEnum(str, enum.Enum):
    """Matches PostgreSQL ``signal_type_enum`` (lowercase labels)."""

    bullish = "bullish"
    bearish = "bearish"
    neutral = "neutral"
    mixed = "mixed"


class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"


class IngestionSourceEnum(str, enum.Enum):
    manual = "manual"
    rss = "rss"
    api = "api"
    scraper = "scraper"
    exchange_feed = "exchange_feed"


class EventSubtype(Base):
    __tablename__ = "event_subtypes"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[EventTypeEnum] = mapped_column(
        _events_enum(EventTypeEnum, "event_type_enum"),
        nullable=False,
    )
    subtype_code: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_signal: Mapped[SignalTypeEnum] = mapped_column(
        _events_enum(SignalTypeEnum, "signal_type_enum"),
        nullable=False,
        default=SignalTypeEnum.neutral,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StoxEventBatch(Base):
    """Batch container for market events (`stoxscoop.event_batches` by default)."""

    __tablename__ = "event_batches"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    ingestion_source: Mapped[IngestionSourceEnum] = mapped_column(
        _events_enum(IngestionSourceEnum, "ingestion_source_enum"),
        nullable=False,
        default=IngestionSourceEnum.manual,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_events: Mapped[int | None] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stox_events = relationship("StoxEvent", back_populates="batch")


class StoxEvent(Base):
    """Core market event row (`stoxscoop.events` by default). Renamed to avoid clashing with legacy `Event`."""

    __tablename__ = "events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["event_type", "event_subtype"],
            [
                f"{EVENTS_SCHEMA}.event_subtypes.event_type",
                f"{EVENTS_SCHEMA}.event_subtypes.subtype_code",
            ],
        ),
        {"schema": EVENTS_SCHEMA},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("classification.ticker_symbol.id", ondelete="CASCADE"), nullable=False)
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.event_batches.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[EventTypeEnum] = mapped_column(
        _events_enum(EventTypeEnum, "event_type_enum"),
        nullable=False,
    )
    event_subtype: Mapped[str] = mapped_column(String(80), nullable=False)
    signal_type: Mapped[SignalTypeEnum] = mapped_column(
        _events_enum(SignalTypeEnum, "signal_type_enum"),
        nullable=False,
        default=SignalTypeEnum.neutral,
    )
    signal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[SentimentEnum] = mapped_column(
        _events_enum(SentimentEnum, "sentiment_enum"),
        nullable=False,
        default=SentimentEnum.neutral,
    )
    priority: Mapped[PriorityEnum] = mapped_column(
        _events_enum(PriorityEnum, "priority_enum"),
        nullable=False,
        default=PriorityEnum.low,
    )
    impact_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 3), nullable=True)
    confidence_model_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), default=list)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ingestion_source: Mapped[IngestionSourceEnum] = mapped_column(
        _events_enum(IngestionSourceEnum, "ingestion_source_enum"),
        nullable=False,
        default=IngestionSourceEnum.manual,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    stock = relationship("Stock", back_populates="events")
    batch = relationship("StoxEventBatch", back_populates="stox_events")


class CorporateActionDetails(Base):
    __tablename__ = "corporate_action_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    record_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ratio: Mapped[str | None] = mapped_column(String(30), nullable=True)
    amount_per_share: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    total_size: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    target_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    swap_ratio: Mapped[str | None] = mapped_column(String(30), nullable=True)
    offer_price: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class DisclosureDetails(Base):
    __tablename__ = "disclosure_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    investor_category: Mapped[str] = mapped_column(String(50), nullable=False)
    investor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    investor_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    transaction_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shares_transacted: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    price_per_share: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    transaction_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    stake_before: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    stake_after: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    transaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    exchange: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class InsiderDetails(Base):
    __tablename__ = "insider_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    person_name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    relationship: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    shares_transacted: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    price_per_share: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    transaction_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    stake_before: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    stake_after: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    pledge_percentage: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    sebi_disclosure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    transaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class BusinessEventDetails(Base):
    __tablename__ = "business_event_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    contract_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contract_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    capex_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    duration_years: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    geography: Mapped[str | None] = mapped_column(String(100), nullable=True)
    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expected_completion: Mapped[date | None] = mapped_column(Date, nullable=True)
    jv_partner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ownership_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_repeat_order: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    campaign_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_revenue: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    target_timeline: Mapped[str | None] = mapped_column(String(50), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_geography: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_segment: Mapped[str | None] = mapped_column(String(255), nullable=True)


class GovernanceDetails(Base):
    __tablename__ = "governance_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    person_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    change_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulator: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    penalty_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    meeting_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    agenda_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class StoxCreditRatingDetails(Base):
    """Renamed to avoid clashing with legacy `CreditRatingDetails` in `event_details.py`."""

    __tablename__ = "credit_rating_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    agency: Mapped[str] = mapped_column(String(30), nullable=False)
    instrument_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    instrument_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating_before: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rating_after: Mapped[str | None] = mapped_column(String(20), nullable=True)
    outlook_before: Mapped[str | None] = mapped_column(String(20), nullable=True)
    outlook_after: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rated_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class FinancialResultDetails(Base):
    __tablename__ = "financial_result_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    period_quarter: Mapped[str | None] = mapped_column(String(5), nullable=True)
    period_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    revenue_yoy_pct: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    ebitda: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    ebitda_margin: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    pat: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    pat_yoy_pct: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    eps: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    beat_miss: Mapped[str | None] = mapped_column(String(10), nullable=True)
    guidance_revenue: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guidance_margin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    key_highlight: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class FundraisingDetails(Base):
    __tablename__ = "fundraising_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    issue_size: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    price_per_share: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    number_of_shares: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    allottee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    allottee_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    coupon_rate: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tenure_years: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    open_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    subscription_times: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class LegalDetails(Base):
    __tablename__ = "legal_details"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey(f"{EVENTS_SCHEMA}.events.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    forum: Mapped[str | None] = mapped_column(String(100), nullable=True)
    case_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    counterparty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    demand_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    penalty_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    company_stance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_hearing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contingent_liability: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

