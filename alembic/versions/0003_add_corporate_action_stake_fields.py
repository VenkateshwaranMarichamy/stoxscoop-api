"""Add stake/share columns to corporate_action_details.

Revision ID: 0003_add_corporate_action_stake_fields
Revises: 0002_add_contract_type
Create Date: 2026-03-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_add_corporate_action_stake_fields"
down_revision = "0002_add_contract_type"
branch_labels = None
depends_on = None

SCHEMA = "stoxscoop"
TABLE = "corporate_action_details"


def _column_exists(bind, column_name: str) -> bool:
    return (
        bind.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = :schema
                  AND table_name = :table
                  AND column_name = :column
                """
            ),
            {"schema": SCHEMA, "table": TABLE, "column": column_name},
        ).first()
        is not None
    )


def upgrade() -> None:
    bind = op.get_bind()

    if not _column_exists(bind, "stake_acquired_pct"):
        op.add_column(
            TABLE,
            sa.Column("stake_acquired_pct", sa.Numeric(5, 2), nullable=True),
            schema=SCHEMA,
        )

    if not _column_exists(bind, "resulting_stake_pct"):
        op.add_column(
            TABLE,
            sa.Column("resulting_stake_pct", sa.Numeric(5, 2), nullable=True),
            schema=SCHEMA,
        )

    if not _column_exists(bind, "shares_transacted"):
        op.add_column(
            TABLE,
            sa.Column("shares_transacted", sa.BigInteger(), nullable=True),
            schema=SCHEMA,
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _column_exists(bind, "shares_transacted"):
        op.drop_column(TABLE, "shares_transacted", schema=SCHEMA)

    if _column_exists(bind, "resulting_stake_pct"):
        op.drop_column(TABLE, "resulting_stake_pct", schema=SCHEMA)

    if _column_exists(bind, "stake_acquired_pct"):
        op.drop_column(TABLE, "stake_acquired_pct", schema=SCHEMA)
