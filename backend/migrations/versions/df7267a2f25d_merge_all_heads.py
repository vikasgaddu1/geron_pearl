"""merge_all_heads

Revision ID: df7267a2f25d
Revises: 2da21039add2, add_status_history
Create Date: 2026-01-05 11:50:18.718404

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df7267a2f25d'
down_revision = ('2da21039add2', 'add_status_history')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass