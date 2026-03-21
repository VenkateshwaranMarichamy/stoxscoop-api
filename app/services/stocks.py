from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.stocks import Stock


def list_stocks(db: Session, *, limit: int = 200, offset: int = 0) -> list[Stock]:
    stmt = (
        select(Stock)
        .where(Stock.is_active.is_(True))
        .order_by(Stock.symbol.asc(), Stock.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars().all())


def list_all_stocks(db: Session) -> list[Stock]:
    stmt = select(Stock).where(Stock.is_active.is_(True)).order_by(Stock.symbol.asc(), Stock.id.asc())
    return list(db.execute(stmt).scalars().all())

