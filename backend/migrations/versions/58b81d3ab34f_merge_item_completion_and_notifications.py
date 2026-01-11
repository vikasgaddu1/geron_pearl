"""merge_item_completion_and_notifications

Revision ID: 58b81d3ab34f
Revises: add_item_type_code_completion, add_notifications_table
Create Date: 2026-01-11 17:57:37.339116

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58b81d3ab34f'
down_revision = ('add_item_type_code_completion', 'add_notifications_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass