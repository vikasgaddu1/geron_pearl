"""merge content column migration

Revision ID: ee7684fa608b
Revises: 81fa70a795df, add_content_to_text_elements
Create Date: 2026-01-06 16:46:37.074138

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee7684fa608b'
down_revision = ('81fa70a795df', 'add_content_to_text_elements')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass