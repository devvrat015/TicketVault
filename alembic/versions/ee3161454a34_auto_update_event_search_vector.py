"""auto update event search vector

Revision ID: ee3161454a34

Revises: ac38cda8a089

Create Date: 2026-09-09 11:44:35.306904

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "ee3161454a34"
down_revision: Union[str, Sequence[str], None] = "ac38cda8a089"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Function that automatically updates search_vector
    op.execute("""
        CREATE FUNCTION update_event_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector :=
                to_tsvector(
                    'english',
                    coalesce(NEW.title, '') || ' ' ||
                    coalesce(NEW.description, '')
                );

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Automatically update search_vector on INSERT
    # or when title/description changes
    op.execute("""
        CREATE TRIGGER events_search_vector_update
        BEFORE INSERT OR UPDATE OF title, description
        ON events
        FOR EACH ROW
        EXECUTE FUNCTION update_event_search_vector();
    """)


def downgrade() -> None:
    """Downgrade schema."""

    op.execute("""
        DROP TRIGGER IF EXISTS events_search_vector_update
        ON events;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS update_event_search_vector();
    """)