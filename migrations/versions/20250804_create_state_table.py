"""Create state table."""

from __future__ import annotations

from alembic import op  # type: ignore[import]
import sqlalchemy as sa  # type: ignore[import]

revision = "20250804_create_state_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "state",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False),
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table("state")
