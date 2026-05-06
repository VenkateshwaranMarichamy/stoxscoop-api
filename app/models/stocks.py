from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StockAlias(Base):
    __tablename__ = "stock_alias"
    __table_args__ = {"schema": "stoxscoop"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey("classification.ticker_symbol.id"), nullable=False)
    alias_name: Mapped[str] = mapped_column(Text, nullable=False)

    stock: Mapped["Stock"] = relationship("Stock", back_populates="aliases")


class Stock(Base):
    __tablename__ = "ticker_symbol"
    __table_args__ = {"schema": "classification"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    symbol: Mapped[str] = mapped_column("trading_symbol", String(50), nullable=False)
    is_active: Mapped[bool | None] = mapped_column("is_active", Boolean, nullable=True)

    events = relationship("StoxEvent", back_populates="stock", cascade="all, delete-orphan")
    aliases: Mapped[list["StockAlias"]] = relationship("StockAlias", back_populates="stock")

