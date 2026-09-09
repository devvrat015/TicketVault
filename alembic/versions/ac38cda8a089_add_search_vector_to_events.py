"""add search vector to events

Revision ID: ac38cda8a089
Revises: 673bd7d4b398
Create Date: 2026-09-08 23:01:35.182776
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "ac38cda8a089"
down_revision: Union[str, Sequence[str], None] = "673bd7d4b398"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Add the search_vector column
    op.add_column(
        "events",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            nullable=True,
        ),
    )

    # 2. Populate search_vector for existing events
    op.execute(
        """
        UPDATE events
        SET search_vector =
            to_tsvector(
                'english',
                coalesce(title, '') || ' ' || coalesce(description, '')
            )
        """
    )

    # 3. Create GIN index
    op.create_index(
        "ix_events_search_vector",
        "events",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove GIN index
    op.drop_index(
        "ix_events_search_vector",
        table_name="events",
    )

    # Remove search_vector column
    op.drop_column(
        "events",
        "search_vector",
    )