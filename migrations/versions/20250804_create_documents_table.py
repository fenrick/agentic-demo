"""Create documents table."""

from __future__ import annotations

import sqlalchemy as sa  # type: ignore[import]
from alembic import op  # type: ignore[import]

revision = "20250804_create_documents_table"
down_revision = "20250804_create_state_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("state_id", sa.Integer, sa.ForeignKey("state.id"), nullable=False),
        sa.Column("parquet_blob", sa.LargeBinary, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table("documents")
