"""add next_meet_at to relationship model

Revision ID: 926a6930fcad
Revises: f797bed9a488
Create Date: 2026-05-05 15:12:21.538499

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "926a6930fcad"
down_revision: str | Sequence[str] | None = "f797bed9a488"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "relationships",
        sa.Column("next_meet_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("relationships", "next_meet_at")
