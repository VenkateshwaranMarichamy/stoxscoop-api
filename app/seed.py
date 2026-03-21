from __future__ import annotations

from datetime import date

from app.db.session import SessionLocal
from app.models.enums import EventType, Priority
from app.models.event_batches import EventBatch
from app.models.event_details import ContractDetails, StakeTransactionDetails
from app.models.events import Event
from app.models.stocks import Stock


def run_seed() -> None:
    db = SessionLocal()
    try:
        reliance = db.query(Stock).filter(Stock.symbol == "RELIANCE").first()
        tcs = db.query(Stock).filter(Stock.symbol == "TCS").first()
        if reliance is None or tcs is None:
            raise RuntimeError("Expected stocks 'RELIANCE' and 'TCS' to exist in classification.ticker_symbol")

        batch = EventBatch(batch_name="Sample Batch - March 2026", notes="Seeded sample events")
        db.add(batch)
        db.flush()

        e1 = Event(
            stock_id=reliance.id,
            batch_id=batch.id,
            event_type=EventType.contract,
            title="Signed multi-year enterprise contract",
            event_date=date(2026, 3, 1),
            priority=Priority.high,
            impact_score=8,
            source_url="https://example.com/contract",
        )
        db.add(e1)
        db.flush()
        db.add(
            ContractDetails(
                event_id=e1.id,
                client_name="Global Enterprise Co.",
                contract_type="CONFIRMED",
                contract_value=250000000.00,
                duration_years=5,
                description="Large-scale digital transformation deal.",
            )
        )

        e2 = Event(
            stock_id=tcs.id,
            batch_id=batch.id,
            event_type=EventType.stake_transaction,
            title="Institutional investor increased stake",
            event_date=date(2026, 3, 5),
            priority=Priority.medium,
            impact_score=6,
            source_url="https://example.com/stake",
        )
        db.add(e2)
        db.flush()
        db.add(
            StakeTransactionDetails(
                event_id=e2.id,
                investor_name="Example Capital",
                transaction_type="BUY",
                stake_percentage=0.42,
                transaction_value=12500000.00,
                price_per_share=3850.25,
                transaction_date=date(2026, 3, 5),
            )
        )

        db.commit()
        print("Seed completed.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

