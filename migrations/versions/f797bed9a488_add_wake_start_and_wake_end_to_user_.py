"""add wake_start and wake_end to user model

Revision ID: f797bed9a488
Revises: 4a190051b739
Create Date: 2026-05-02 11:00:43.120826

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f797bed9a488"
down_revision: str | Sequence[str] | None = "4a190051b739"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "wake_start",
            sa.Integer(),
            nullable=False,
            server_default="420",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "wake_end",
            sa.Integer(),
            nullable=False,
            server_default="1320",
        ),
    )

    op.alter_column("users", "wake_start", server_default=None)
    op.alter_column("users", "wake_end", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "wake_end")
    op.drop_column("users", "wake_start")
