from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.v1 import EventTypeEnum, IngestionSourceEnum, PriorityEnum, SentimentEnum, SignalTypeEnum
from app.schemas.common import APIModel


def _coerce_signal_type_input(v: Any) -> Any:
    """Normalize client input to lowercase enum strings for ``signal_type``."""
    if v is None:
        return v
    if isinstance(v, SignalTypeEnum):
        return v
    if isinstance(v, str):
        return v.strip().lower()
    return v


def _coerce_lowercase_str_for_pg_enum(v: Any, enum_cls: type) -> Any:
    """Lowercase string labels for PostgreSQL ENUM columns (any casing from UI)."""
    if v is None:
        return v
    if isinstance(v, enum_cls):
        return v
    if isinstance(v, str):
        return v.strip().lower()
    return v


class BatchCreate(BaseModel):
    batch_name: str = Field(min_length=1, max_length=255)
    notes: str | None = None


class BatchRead(APIModel):
    id: int
    batch_name: str
    ingestion_source: IngestionSourceEnum
    notes: str | None
    started_at: datetime
    completed_at: datetime | None
    total_events: int | None
    created_at: datetime
    updated_at: datetime | None


class EventCreate(BaseModel):
    stock_id: int
    batch_id: int | None = None
    event_type: EventTypeEnum
    event_subtype: str = Field(min_length=1, max_length=80)
    event_date: date
    title: str = Field(min_length=1, max_length=500)
    summary: str | None = None
    signal_type: SignalTypeEnum | None = None
    signal_reason: str | None = None
    sentiment: SentimentEnum | None = None
    priority: PriorityEnum | None = None
    impact_score: int | None = Field(default=None, ge=1, le=100)
    source_url: str | None = None
    source_name: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = None
    detail: dict[str, Any] | None = None

    @field_validator("signal_type", mode="before")
    @classmethod
    def normalize_signal_type(cls, v: Any) -> Any:
        """Accept any casing; stored values match lowercase ``signal_type_enum``."""
        return _coerce_signal_type_input(v)

    @field_validator("event_type", mode="before")
    @classmethod
    def normalize_event_type(cls, v: Any) -> Any:
        return _coerce_lowercase_str_for_pg_enum(v, EventTypeEnum)

    @field_validator("event_subtype", mode="before")
    @classmethod
    def normalize_event_subtype(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment(cls, v: Any) -> Any:
        return _coerce_lowercase_str_for_pg_enum(v, SentimentEnum)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v: Any) -> Any:
        return _coerce_lowercase_str_for_pg_enum(v, PriorityEnum)


class EventBatchCreate(BaseModel):
    batch_id: int | None = None
    events: list[EventCreate]

    @model_validator(mode="before")
    @classmethod
    def coerce_single_event_payload(cls, data: Any) -> Any:
        """Allow posting one event object to ``POST /events/batch`` (same shape as ``EventCreate`` + optional top-level ``batch_id``)."""
        if not isinstance(data, dict):
            return data
        if "events" in data:
            return data
        if "stock_id" in data:
            batch_id = data.get("batch_id")
            event_only = {k: v for k, v in data.items() if k != "batch_id"}
            return {"batch_id": batch_id, "events": [event_only]}
        return data


class BatchWithEventsCreate(BaseModel):
    batch_name: str = Field(min_length=1, max_length=255)
    notes: str | None = None
    events: list[EventCreate]


class EventRead(APIModel):
    id: int
    stock_id: int
    batch_id: int | None
    event_type: EventTypeEnum
    event_subtype: str
    signal_type: SignalTypeEnum
    signal_reason: str | None
    sentiment: SentimentEnum
    priority: PriorityEnum
    impact_score: int | None
    confidence_score: float | None
    confidence_model_version: str | None
    tags: list[str] | None
    title: str
    summary: str | None
    event_date: date
    source_url: str | None
    source_name: str | None
    ingestion_source: IngestionSourceEnum
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    detail: dict[str, Any] | None = None


class EventResultItem(APIModel):
    index: int
    status: str  # "created" | "failed"
    id: int | None = None
    error: str | None = None


class BatchWithEventsPartialRead(APIModel):
    batch: BatchRead
    created: int
    failed: int
    results: list[EventResultItem]


class BatchWithEventsRead(APIModel):
    batch: BatchRead
    events: list[EventRead]


class EventUpdate(BaseModel):
    event_date: date | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    summary: str | None = None
    signal_type: SignalTypeEnum | None = None
    signal_reason: str | None = None
    sentiment: SentimentEnum | None = None
    priority: PriorityEnum | None = None
    impact_score: int | None = Field(default=None, ge=1, le=100)
    source_url: str | None = None
    source_name: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = None
    detail: dict[str, Any] | None = None
    is_verified: bool | None = None

    @field_validator("signal_type", mode="before")
    @classmethod
    def normalize_signal_type_update(cls, v: Any) -> Any:
        return _coerce_signal_type_input(v)

    @field_validator("sentiment", mode="before")
    @classmethod
    def normalize_sentiment_update(cls, v: Any) -> Any:
        return _coerce_lowercase_str_for_pg_enum(v, SentimentEnum)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority_update(cls, v: Any) -> Any:
        return _coerce_lowercase_str_for_pg_enum(v, PriorityEnum)


class SubtypeRead(APIModel):
    event_type: EventTypeEnum
    subtype_code: str
    label: str
    description: str | None
    default_signal: SignalTypeEnum

