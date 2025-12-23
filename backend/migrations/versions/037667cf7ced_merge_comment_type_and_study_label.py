"""merge_comment_type_and_study_label

Revision ID: 037667cf7ced
Revises: a1b2c3d4e5f6, unique_study_label
Create Date: 2025-12-16 13:02:38.146127

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '037667cf7ced'
down_revision = ('a1b2c3d4e5f6', 'unique_study_label')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass