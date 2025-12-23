"""Add comment_type column to tracker_comments

Revision ID: a1b2c3d4e5f6
Revises: f5a535fcf5e5
Create Date: 2025-12-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f5a535fcf5e5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add comment_type column with default 'programming'
    op.add_column(
        'tracker_comments',
        sa.Column('comment_type', sa.String(length=20), nullable=False, server_default='programming')
    )
    
    # Create index for efficient filtering
    op.create_index(
        'ix_tracker_comments_comment_type',
        'tracker_comments',
        ['comment_type']
    )
    
    # Backfill existing comments as 'programming' (already done by server_default)
    # No explicit update needed since server_default handles it


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_tracker_comments_comment_type', table_name='tracker_comments')
    
    # Drop the column
    op.drop_column('tracker_comments', 'comment_type')


