"""Initial drift engine schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "baselines",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_baselines_name_version", "baselines", ["name", "version"], unique=True)

    op.create_table(
        "snapshots",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_snapshots_source_collected_at", "snapshots", ["source", "collected_at"])

    op.create_table(
        "drift_reports",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("baseline_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_drift_reports_baseline_id", "drift_reports", ["baseline_id"])
    op.create_index("ix_drift_reports_generated_at", "drift_reports", ["generated_at"])

    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policies")
    op.drop_index("ix_drift_reports_generated_at", table_name="drift_reports")
    op.drop_index("ix_drift_reports_baseline_id", table_name="drift_reports")
    op.drop_table("drift_reports")
    op.drop_index("ix_snapshots_source_collected_at", table_name="snapshots")
    op.drop_table("snapshots")
    op.drop_index("ix_baselines_name_version", table_name="baselines")
    op.drop_table("baselines")
