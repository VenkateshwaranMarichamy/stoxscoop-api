from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import APIModel


class MarketUpdateCreate(APIModel):
    title: str = Field(min_length=1)
    content: str | None = None
    summary: str | None = None
    source: str | None = Field(default=None, max_length=255)
    url: str | None = None
    published_at: datetime | None = None
    basic_ind_codes: list[str] | None = None
    sentiment: str | None = Field(default=None, max_length=20)
    category: str | None = Field(default=None, max_length=100)
    impact: str | None = Field(default=None, max_length=10)
    tags: list[str] | None = None
    entities: list[str] | None = None
    metrics: dict[str, Any] | None = None
    importance_score: float | None = None


class MarketUpdateRead(APIModel):
    id: int
    title: str
    content: str | None
    summary: str | None
    source: str | None
    url: str | None
    published_at: datetime | None
    ingested_at: datetime | None
    basic_ind_codes: list[str] | None
    sentiment: str | None
    category: str | None
    impact: str | None
    tags: list[str] | None
    entities: list[str] | None
    metrics: dict[str, Any] | None
    importance_score: float | None


class MarketUpdateUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1)
    content: str | None = None
    summary: str | None = None
    source: str | None = Field(default=None, max_length=255)
    url: str | None = None
    published_at: datetime | None = None
    basic_ind_codes: list[str] | None = None
    sentiment: str | None = Field(default=None, max_length=20)
    category: str | None = Field(default=None, max_length=100)
    impact: str | None = Field(default=None, max_length=10)
    tags: list[str] | None = None
    entities: list[str] | None = None
    metrics: dict[str, Any] | None = None
    importance_score: float | None = None
