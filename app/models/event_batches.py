from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventBatch(Base):
    __tablename__ = "event_batches"
    __table_args__ = {"schema": "stoxscoop"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    events = relationship("Event", back_populates="batch", cascade="all, delete-orphan")

