"""Create lectures table."""

from __future__ import annotations

import sqlalchemy as sa  # type: ignore[import]
from alembic import op  # type: ignore[import]

revision = "20250806_create_lectures_table"
down_revision = "20250805_create_citations_action_logs_metrics_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "lectures",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("lecture_json", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table("lectures")
