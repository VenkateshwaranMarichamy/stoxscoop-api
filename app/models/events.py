from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EventType, Priority


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "stoxscoop"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("classification.ticker_symbol.id", ondelete="CASCADE"), nullable=False, index=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        ForeignKey("stoxscoop.event_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )

    event_type: Mapped[EventType] = mapped_column(
        ENUM(
            EventType,
            name="stock_event_type",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    priority: Mapped[Priority] = mapped_column(
        ENUM(
            Priority,
            name="priority",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    impact_score: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    stock = relationship("Stock", back_populates="events")
    batch = relationship("EventBatch", back_populates="events")

    stake_transaction_details = relationship(
        "StakeTransactionDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    contract_details = relationship(
        "ContractDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    buyback_details = relationship(
        "BuybackDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    acquisition_details = relationship(
        "AcquisitionDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    pledge_details = relationship("PledgeDetails", back_populates="event", uselist=False, cascade="all, delete-orphan")
    insider_trading_details = relationship(
        "InsiderTradingDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    sebi_action_details = relationship(
        "SebiActionDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    fii_dii_details = relationship(
        "FiiDiiDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    mutual_fund_details = relationship(
        "MutualFundDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    credit_rating_details = relationship(
        "CreditRatingDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    auditor_resignation_details = relationship(
        "AuditorResignationDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
    board_change_details = relationship(
        "BoardChangeDetails", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )

