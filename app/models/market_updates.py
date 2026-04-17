from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, Float, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.base import Base

EVENTS_SCHEMA = settings.events_schema


class MarketUpdate(Base):
    __tablename__ = "market_updates"
    __table_args__ = {"schema": EVENTS_SCHEMA}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, server_default=func.now())
    basic_ind_codes: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    impact: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    entities: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
