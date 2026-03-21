from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.stocks import StockRead
from app.services.stocks import list_all_stocks, list_stocks


router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockRead])
def list_(  # noqa: ANN201
    limit: int = Query(6000, ge=1, le=20000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_stocks(db, limit=limit, offset=offset)


@router.get("/all", response_model=list[StockRead])
def all_(db: Session = Depends(get_db)) -> list[StockRead]:
    return list_all_stocks(db)

