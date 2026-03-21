from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class StockCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    symbol: str = Field(min_length=1, max_length=50)


class StockRead(APIModel):
    id: int
    name: str
    symbol: str

