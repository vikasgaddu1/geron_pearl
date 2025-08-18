"""Remove is_deleted column from tracker_comments

Revision ID: f5a535fcf5e5
Revises: 07fb820f6a75
Create Date: 2025-08-18 10:07:27.209294

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5a535fcf5e5'
down_revision = '07fb820f6a75'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop is_deleted column from tracker_comments table
    op.drop_column('tracker_comments', 'is_deleted')


def downgrade() -> None:
    # Add back is_deleted column if needed for rollback
    op.add_column('tracker_comments', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))