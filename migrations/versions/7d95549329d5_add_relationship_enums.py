"""add relationship enums

Revision ID: 7d95549329d5
Revises: b5d6fa8e06f1
Create Date: 2025-09-09 13:08:38.674063
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7d95549329d5"
down_revision: str | Sequence[str] | None = "b5d6fa8e06f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Explicitly create enum types first so Postgres can use them in ALTER COLUMN
    op.execute("CREATE TYPE relationship_type AS ENUM ('romantic','friendship','family');")
    op.execute("CREATE TYPE relationship_status AS ENUM ('active','inactive','pending','ended');")

    # Now alter columns, casting existing text values to the new enum types
    op.alter_column(
        "relationships",
        "type",
        existing_type=sa.VARCHAR(length=120),
        type_=postgresql.ENUM(
            "romantic", "friendship", "family", name="relationship_type", create_type=False
        ),
        existing_nullable=False,
        postgresql_using="type::text::relationship_type",
    )

    op.alter_column(
        "relationships",
        "status",
        existing_type=sa.VARCHAR(length=120),
        type_=postgresql.ENUM(
            "active", "inactive", "pending", "ended", name="relationship_status", create_type=False
        ),
        existing_nullable=False,
        postgresql_using="status::text::relationship_status",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert columns back to VARCHAR first
    op.alter_column(
        "relationships",
        "status",
        existing_type=postgresql.ENUM(
            "active", "inactive", "pending", "ended", name="relationship_status", create_type=False
        ),
        type_=sa.VARCHAR(length=120),
        existing_nullable=False,
        postgresql_using="status::text",
    )

    op.alter_column(
        "relationships",
        "type",
        existing_type=postgresql.ENUM(
            "romantic", "friendship", "family", name="relationship_type", create_type=False
        ),
        type_=sa.VARCHAR(length=120),
        existing_nullable=False,
        postgresql_using="type::text",
    )

    # Drop enum types
    op.execute("DROP TYPE relationship_status;")
    op.execute("DROP TYPE relationship_type;")
