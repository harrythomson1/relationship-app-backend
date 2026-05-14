"""add ended to invite_status enum

Revision ID: 59a1b7858f48
Revises: 9f9d920ddd70
Create Date: 2026-05-15 00:17:33.199149

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "59a1b7858f48"
down_revision: str | Sequence[str] | None = "9f9d920ddd70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE invite_status ADD VALUE IF NOT EXISTS 'ended'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres does not support removing values from an enum without
    # rebuilding the type. Leave the value in place on downgrade — it is
    # harmless as long as no rows use it.
    pass
