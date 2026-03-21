"""Initial schema for stocks, batches, events, and details.

Revision ID: 0001_init_schema
Revises: 
Create Date: 2026-03-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS stoxscoop")

    stock_event_type_enum = postgresql.ENUM(
        "STAKE_TRANSACTION",
        "CONTRACT",
        "BUYBACK",
        "ACQUISITION",
        "PLEDGE",
        "INSIDER_TRADING",
        "SEBI_ACTION",
        "FII_DII",
        "MUTUAL_FUND",
        "CREDIT_RATING",
        "AUDITOR_RESIGNATION",
        "BOARD_CHANGE",
        name="stock_event_type",
        create_type=False,
    )
    priority_enum = postgresql.ENUM("HIGH", "MEDIUM", "LOW", name="priority", create_type=False)

    stock_event_type_enum.create(op.get_bind(), checkfirst=True)
    priority_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "event_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_name", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="stoxscoop",
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("stock_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("event_type", stock_event_type_enum, nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("priority", priority_enum, nullable=False),
        sa.Column("impact_score", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["stoxscoop.event_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["stock_id"], ["classification.ticker_symbol.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )
    op.create_index("ix_events_stock_id", "events", ["stock_id"], schema="stoxscoop")
    op.create_index("ix_events_event_date", "events", ["event_date"], schema="stoxscoop")
    op.create_index("ix_events_event_type", "events", ["event_type"], schema="stoxscoop")
    op.create_index("ix_events_batch_id", "events", ["batch_id"], schema="stoxscoop")

    op.create_table(
        "stake_transaction_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("investor_name", sa.String(length=255), nullable=False),
        sa.Column("transaction_type", sa.String(length=100), nullable=False),
        sa.Column("stake_percentage", sa.Float(), nullable=True),
        sa.Column("transaction_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("price_per_share", sa.Numeric(18, 4), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "contract_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("contract_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("duration_years", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "buyback_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("buyback_type", sa.String(length=100), nullable=True),
        sa.Column("buyback_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("total_size", sa.Numeric(18, 2), nullable=True),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "acquisition_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("target_company", sa.String(length=255), nullable=False),
        sa.Column("deal_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("stake_percentage", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "pledge_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("promoter_name", sa.String(length=255), nullable=False),
        sa.Column("before_percentage", sa.Float(), nullable=True),
        sa.Column("after_percentage", sa.Float(), nullable=True),
        sa.Column("change_type", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "insider_trading_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("insider_name", sa.String(length=255), nullable=False),
        sa.Column("designation", sa.String(length=255), nullable=True),
        sa.Column("transaction_type", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(18, 4), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "sebi_action_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("action_type", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("penalty_amount", sa.Numeric(18, 2), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "fii_dii_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("investor_type", sa.String(length=50), nullable=False),
        sa.Column("transaction_type", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "mutual_fund_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("fund_name", sa.String(length=255), nullable=False),
        sa.Column("transaction_type", sa.String(length=100), nullable=False),
        sa.Column("stake_change", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "credit_rating_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("agency", sa.String(length=255), nullable=False),
        sa.Column("rating_before", sa.String(length=50), nullable=True),
        sa.Column("rating_after", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "auditor_resignation_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("auditor_name", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )

    op.create_table(
        "board_change_details",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("person_name", sa.String(length=255), nullable=False),
        sa.Column("designation", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["stoxscoop.events.id"], ondelete="CASCADE"),
        schema="stoxscoop",
    )


def downgrade() -> None:
    op.drop_table("board_change_details", schema="stoxscoop")
    op.drop_table("auditor_resignation_details", schema="stoxscoop")
    op.drop_table("credit_rating_details", schema="stoxscoop")
    op.drop_table("mutual_fund_details", schema="stoxscoop")
    op.drop_table("fii_dii_details", schema="stoxscoop")
    op.drop_table("sebi_action_details", schema="stoxscoop")
    op.drop_table("insider_trading_details", schema="stoxscoop")
    op.drop_table("pledge_details", schema="stoxscoop")
    op.drop_table("acquisition_details", schema="stoxscoop")
    op.drop_table("buyback_details", schema="stoxscoop")
    op.drop_table("contract_details", schema="stoxscoop")
    op.drop_table("stake_transaction_details", schema="stoxscoop")

    op.drop_index("ix_events_batch_id", table_name="events", schema="stoxscoop")
    op.drop_index("ix_events_event_type", table_name="events", schema="stoxscoop")
    op.drop_index("ix_events_event_date", table_name="events", schema="stoxscoop")
    op.drop_index("ix_events_stock_id", table_name="events", schema="stoxscoop")
    op.drop_table("events", schema="stoxscoop")
    op.drop_table("event_batches", schema="stoxscoop")

    op.execute("DROP TYPE IF EXISTS priority")
    op.execute("DROP TYPE IF EXISTS stock_event_type")

