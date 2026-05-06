from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.stocks import Stock, StockAlias


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


def list_stocks_with_aliases(db: Session) -> list[dict]:
    """Return active stocks as {id, names} where names = [canonical_name, ...alias_names]."""
    stmt = (
        select(Stock)
        .where(Stock.is_active.is_(True))
        .options(selectinload(Stock.aliases))
        .order_by(Stock.id.asc())
    )
    stocks = db.execute(stmt).scalars().all()
    result = []
    for stock in stocks:
        names = [stock.name] + [a.alias_name for a in stock.aliases]
        result.append({"id": stock.id, "names": names})
    return result

