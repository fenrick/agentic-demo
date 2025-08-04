"""Create citations table."""

from __future__ import annotations

import sqlalchemy as sa  # type: ignore[import]
from alembic import op  # type: ignore[import]

revision = "0001"
down_revision = None
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


def downgrade() -> None:
    """Revert the migration."""

    op.drop_table("citations")
