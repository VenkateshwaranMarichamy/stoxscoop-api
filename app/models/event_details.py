from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StakeTransactionDetails(Base):
    __tablename__ = "stake_transaction_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    investor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(100), nullable=False)
    stake_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    transaction_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    price_per_share: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    transaction_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    event = relationship("Event", back_populates="stake_transaction_details")


class ContractDetails(Base):
    __tablename__ = "contract_details"
    __table_args__ = (
        CheckConstraint(
            "contract_type IN ('CONFIRMED', 'MOU', 'STRATEGIC_PARTNERSHIP')",
            name="ck_contract_details_contract_type",
        ),
        {"schema": "stoxscoop"},
    )

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(50), nullable=True)
    contract_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    duration_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    event = relationship("Event", back_populates="contract_details")


class BuybackDetails(Base):
    __tablename__ = "buyback_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    buyback_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    buyback_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    total_size: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    record_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    event = relationship("Event", back_populates="buyback_details")


class AcquisitionDetails(Base):
    __tablename__ = "acquisition_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    target_company: Mapped[str] = mapped_column(String(255), nullable=False)
    deal_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    stake_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    event = relationship("Event", back_populates="acquisition_details")


class PledgeDetails(Base):
    __tablename__ = "pledge_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    promoter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    before_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    after_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    event = relationship("Event", back_populates="pledge_details")


class InsiderTradingDetails(Base):
    __tablename__ = "insider_trading_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    insider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    event = relationship("Event", back_populates="insider_trading_details")


class SebiActionDetails(Base):
    __tablename__ = "sebi_action_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    penalty_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    event = relationship("Event", back_populates="sebi_action_details")


class FiiDiiDetails(Base):
    __tablename__ = "fii_dii_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    investor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    event = relationship("Event", back_populates="fii_dii_details")


class MutualFundDetails(Base):
    __tablename__ = "mutual_fund_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    fund_name: Mapped[str] = mapped_column(String(255), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(100), nullable=False)
    stake_change: Mapped[float | None] = mapped_column(Float, nullable=True)

    event = relationship("Event", back_populates="mutual_fund_details")


class CreditRatingDetails(Base):
    __tablename__ = "credit_rating_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    agency: Mapped[str] = mapped_column(String(255), nullable=False)
    rating_before: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating_after: Mapped[str | None] = mapped_column(String(50), nullable=True)

    event = relationship("Event", back_populates="credit_rating_details")


class AuditorResignationDetails(Base):
    __tablename__ = "auditor_resignation_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    auditor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    event = relationship("Event", back_populates="auditor_resignation_details")


class BoardChangeDetails(Base):
    __tablename__ = "board_change_details"
    __table_args__ = {"schema": "stoxscoop"}

    event_id: Mapped[int] = mapped_column(ForeignKey("stoxscoop.events.id", ondelete="CASCADE"), primary_key=True)
    person_name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    event = relationship("Event", back_populates="board_change_details")

