"""merge heads after db release date

Revision ID: 81fa70a795df
Revises: add_database_release_date, convert_role_to_is_admin
Create Date: 2026-01-06 16:15:38.182621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81fa70a795df'
down_revision = ('add_database_release_date', 'convert_role_to_is_admin')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass