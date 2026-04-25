"""add updated_at trigger

Revision ID: 4a190051b739
Revises: c6b10bd8e7cf
Create Date: 2026-04-25 12:33:57.986502

"""

from collections.abc import Sequence

from alembic import op

revision: str = "4a190051b739"
down_revision: str | Sequence[str] | None = "c6b10bd8e7cf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ["users", "relationships", "relationship_members", "invites"]


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    for table in _TABLES:
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """
        )


def downgrade() -> None:
    for table in _TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table};")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at;")
