"""Add item_description to reporting_effort_items

Revision ID: c3d4e5f6g7h8
Revises: 0834b59921a2
Create Date: 2026-01-05 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = '0834b59921a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add item_description column to reporting_effort_items table
    op.add_column(
        'reporting_effort_items',
        sa.Column('item_description', sa.String(500), nullable=True)
    )


def downgrade() -> None:
    # Remove item_description column
    op.drop_column('reporting_effort_items', 'item_description')







