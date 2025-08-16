"""remove comment system for redesign

Revision ID: 686b7f37d8ad
Revises: 0b87c8f59a0e
Create Date: 2025-08-16 17:23:38.330119

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '686b7f37d8ad'
down_revision = '0b87c8f59a0e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop comment-related indexes
    op.drop_index('ix_reporting_effort_tracker_comments_comment_type', table_name='reporting_effort_tracker_comments')
    op.drop_index('ix_reporting_effort_tracker_comments_user_id', table_name='reporting_effort_tracker_comments')
    op.drop_index('ix_reporting_effort_tracker_comments_tracker_id', table_name='reporting_effort_tracker_comments')
    
    # Drop the comment table
    op.drop_table('reporting_effort_tracker_comments')


def downgrade() -> None:
    # Recreate the comment table (for rollback purposes)
    op.create_table('reporting_effort_tracker_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('comment_type', sa.Enum('qc_comment', 'prod_comment', 'biostat_comment', name='commenttype'), nullable=False),
        sa.Column('tracked', sa.Boolean(), nullable=True),
        sa.Column('addressed', sa.Boolean(), nullable=True),
        sa.Column('addressed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('addressed_at', sa.DateTime(), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['addressed_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['reporting_effort_tracker_comments.id'], ),
        sa.ForeignKeyConstraint(['tracker_id'], ['reporting_effort_item_tracker.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Recreate indexes
    op.create_index('ix_reporting_effort_tracker_comments_tracker_id', 'reporting_effort_tracker_comments', ['tracker_id'], unique=False)
    op.create_index('ix_reporting_effort_tracker_comments_user_id', 'reporting_effort_tracker_comments', ['user_id'], unique=False)
    op.create_index('ix_reporting_effort_tracker_comments_comment_type', 'reporting_effort_tracker_comments', ['comment_type'], unique=False)