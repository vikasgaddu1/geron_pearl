"""create simplified comment system

Revision ID: 07fb820f6a75
Revises: f29030561d08
Create Date: 2025-08-18 08:54:33.108465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07fb820f6a75'
down_revision = 'f29030561d08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, drop any existing comment tables if they exist
    op.execute("DROP TABLE IF EXISTS tracker_comments CASCADE")
    op.execute("DROP TABLE IF EXISTS reporting_effort_tracker_comments CASCADE")
    op.execute("DROP TYPE IF EXISTS commenttype")
    
    # Remove unresolved_comment_count from reporting_effort_item_tracker if it exists
    try:
        op.drop_index('ix_reporting_effort_item_tracker_unresolved_comment_count', table_name='reporting_effort_item_tracker')
    except:
        pass
    try:
        op.drop_column('reporting_effort_item_tracker', 'unresolved_comment_count')
    except:
        pass
    
    # Create simplified tracker_comments table
    op.create_table('tracker_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['tracker_comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['tracker_id'], ['reporting_effort_item_tracker.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_tracker_comments_id', 'tracker_comments', ['id'])
    op.create_index('ix_tracker_comments_tracker_id', 'tracker_comments', ['tracker_id'])
    op.create_index('ix_tracker_comments_user_id', 'tracker_comments', ['user_id'])
    op.create_index('ix_tracker_comments_parent_comment_id', 'tracker_comments', ['parent_comment_id'])
    op.create_index('ix_tracker_comments_is_resolved', 'tracker_comments', ['is_resolved'])
    op.create_index('ix_tracker_comments_created_at', 'tracker_comments', ['created_at'])
    
    # Add unresolved_comment_count to reporting_effort_item_tracker
    op.add_column('reporting_effort_item_tracker', 
                  sa.Column('unresolved_comment_count', sa.Integer(), nullable=False, default=0))
    op.create_index('ix_reporting_effort_item_tracker_unresolved_comment_count', 
                    'reporting_effort_item_tracker', ['unresolved_comment_count'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_reporting_effort_item_tracker_unresolved_comment_count', table_name='reporting_effort_item_tracker')
    op.drop_index('ix_tracker_comments_created_at', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_is_resolved', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_parent_comment_id', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_user_id', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_tracker_id', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_id', table_name='tracker_comments')
    
    # Drop column and table
    op.drop_column('reporting_effort_item_tracker', 'unresolved_comment_count')
    op.drop_table('tracker_comments')