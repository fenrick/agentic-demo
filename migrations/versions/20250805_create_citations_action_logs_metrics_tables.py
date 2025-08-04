"""Create citations, action_logs, metrics and report tables."""

from __future__ import annotations

import sqlalchemy as sa  # type: ignore[import]
from alembic import op  # type: ignore[import]

revision = "20250805_create_citations_action_logs_metrics_tables"
down_revision = "20250804_create_documents_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "citations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("url", sa.String, nullable=False, unique=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("retrieved_at", sa.DateTime, nullable=False),
        sa.Column("licence", sa.String, nullable=False),
    )

    op.create_table(
        "action_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("agent_name", sa.String, nullable=False),
        sa.Column("input_hash", sa.String, nullable=False),
        sa.Column("output_hash", sa.String, nullable=False),
        sa.Column("tokens", sa.Integer, nullable=False),
        sa.Column("cost", sa.Float, nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
    )

    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
    )

    op.create_table(
        "critique_report",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, nullable=False),
        sa.Column("bloom_coverage_score", sa.Float, nullable=False),
        sa.Column("activity_diversity_score", sa.Float, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_table(
        "factcheck_report",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version_id", sa.Integer, nullable=False),
        sa.Column("unsupported_claim_count", sa.Integer, nullable=False),
        sa.Column("regex_flags", sa.Text, nullable=True),
        sa.Column("cleanlab_scores", sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table("factcheck_report")
    op.drop_table("critique_report")
    op.drop_table("metrics")
    op.drop_table("action_logs")
    op.drop_table("citations")
