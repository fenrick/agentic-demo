"""Create retrieval_cache table."""

from __future__ import annotations

import sqlalchemy as sa  # type: ignore[import]
from alembic import op  # type: ignore[import]

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "retrieval_cache",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("query", sa.String, nullable=False, unique=True),
        sa.Column("results", sa.Text, nullable=False),
        sa.Column("hit_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    """Revert the migration."""

    op.drop_table("retrieval_cache")
