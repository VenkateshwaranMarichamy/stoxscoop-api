from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stocks import StockWithAliasesRead
from app.services.stocks import list_stocks_with_aliases


router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/names", response_model=list[StockWithAliasesRead])
def get_stock_names(db: Session = Depends(get_db)) -> list[StockWithAliasesRead]:
    """Returns all active stocks with their canonical name and aliases combined in a names array."""
    return list_stocks_with_aliases(db)
