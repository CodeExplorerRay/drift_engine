"""Add remediation execution idempotency guards.

Revision ID: 0003_remediation_idempotency
Revises: 0002_operational_tables
Create Date: 2026-04-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_remediation_idempotency"
down_revision: str | None = "0002_operational_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ux_remediation_actions_report_fingerprint",
        "remediation_actions",
        ["report_id", "fingerprint"],
        unique=True,
    )
    op.create_table(
        "remediation_executions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("report_id", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ux_remediation_executions_idempotency",
        "remediation_executions",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_remediation_executions_idempotency",
        table_name="remediation_executions",
    )
    op.drop_table("remediation_executions")
    op.drop_index(
        "ux_remediation_actions_report_fingerprint",
        table_name="remediation_actions",
    )
