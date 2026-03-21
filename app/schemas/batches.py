from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class BatchCreate(BaseModel):
    batch_name: str = Field(min_length=1, max_length=255)
    notes: str | None = None


class BatchRead(APIModel):
    id: int
    batch_name: str
    notes: str | None
    created_at: datetime


class BatchWithEventsCreate(BatchCreate):
    events: list["EventCreate"]


class BatchWithEventsRead(APIModel):
    batch: BatchRead
    events: list["EventRead"]


from app.schemas.events import EventCreate, EventRead  # noqa: E402

