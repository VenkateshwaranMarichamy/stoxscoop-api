"""Add contract_type to contract_details.

Revision ID: 0002_add_contract_type
Revises: 0001_init_schema
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_contract_type"
down_revision = "0001_init_schema"
branch_labels = None
depends_on = None


CONTRACT_TYPE_VALUES = ("CONFIRMED", "MOU", "STRATEGIC_PARTNERSHIP")


def upgrade() -> None:
    bind = op.get_bind()

    # If the previous attempt partially applied the column before failing,
    # re-running should be safe.
    column_exists = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"schema": "stoxscoop", "table": "contract_details", "column": "contract_type"},
    ).first() is not None

    if not column_exists:
        op.add_column(
            "contract_details",
            sa.Column("contract_type", sa.String(length=50), nullable=True),
            schema="stoxscoop",
        )

    constraint_exists = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_constraint
            WHERE conname = :conname
            """
        ),
        {"conname": "ck_contract_details_contract_type"},
    ).first() is not None

    if not constraint_exists:
        op.create_check_constraint(
            "ck_contract_details_contract_type",
            "contract_details",
            "contract_type IN ('CONFIRMED', 'MOU', 'STRATEGIC_PARTNERSHIP')",
            schema="stoxscoop",
        )


def downgrade() -> None:
    bind = op.get_bind()

    constraint_exists = bind.execute(
        sa.text("SELECT 1 FROM pg_constraint WHERE conname = :conname"),
        {"conname": "ck_contract_details_contract_type"},
    ).first() is not None

    if constraint_exists:
        op.drop_constraint(
            "ck_contract_details_contract_type",
            "contract_details",
            schema="stoxscoop",
        )

    column_exists = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"schema": "stoxscoop", "table": "contract_details", "column": "contract_type"},
    ).first() is not None

    if column_exists:
        op.drop_column("contract_details", "contract_type", schema="stoxscoop")

