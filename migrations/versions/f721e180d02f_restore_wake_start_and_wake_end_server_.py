"""restore wake_start and wake_end server defaults

Revision ID: f721e180d02f
Revises: 926a6930fcad
Create Date: 2026-05-14 12:02:57.308886

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f721e180d02f"
down_revision: str | Sequence[str] | None = "926a6930fcad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("users", "wake_start", server_default="420")
    op.alter_column("users", "wake_end", server_default="1320")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "wake_start", server_default=None)
    op.alter_column("users", "wake_end", server_default=None)
