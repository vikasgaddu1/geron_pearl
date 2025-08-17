"""create new tracker comment system

Revision ID: ccff86bd596b
Revises: 686b7f37d8ad
Create Date: 2025-08-16 17:33:20.868475

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ccff86bd596b'
down_revision = 'd3f89a2c4b56'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create comment type enum (only if it doesn't exist)
    op.execute("DO $$ BEGIN CREATE TYPE commenttype AS ENUM ('qc_comment', 'prod_comment', 'biostat_comment'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create tracker_comments table manually to avoid enum creation issues
    op.execute("""
        CREATE TABLE IF NOT EXISTS tracker_comments (
            id SERIAL PRIMARY KEY,
            tracker_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            parent_comment_id INTEGER,
            comment_text TEXT NOT NULL,
            comment_type commenttype NOT NULL,
            is_resolved BOOLEAN NOT NULL DEFAULT false,
            is_pinned BOOLEAN NOT NULL DEFAULT false,
            is_tracked BOOLEAN NOT NULL DEFAULT false,
            is_deleted BOOLEAN NOT NULL DEFAULT false,
            resolved_by_user_id INTEGER,
            resolved_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            FOREIGN KEY (parent_comment_id) REFERENCES tracker_comments(id) ON DELETE CASCADE,
            FOREIGN KEY (resolved_by_user_id) REFERENCES users(id),
            FOREIGN KEY (tracker_id) REFERENCES reporting_effort_item_tracker(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Create indexes for performance
    op.create_index('ix_tracker_comments_tracker_id', 'tracker_comments', ['tracker_id'])
    op.create_index('ix_tracker_comments_user_id', 'tracker_comments', ['user_id'])
    op.create_index('ix_tracker_comments_comment_type', 'tracker_comments', ['comment_type'])
    op.create_index('ix_tracker_comments_parent_comment_id', 'tracker_comments', ['parent_comment_id'])
    op.create_index('ix_tracker_comments_created_at', 'tracker_comments', ['created_at'])
    op.create_index('ix_tracker_comments_is_resolved', 'tracker_comments', ['is_resolved'])
    op.create_index('ix_tracker_comments_is_pinned', 'tracker_comments', ['is_pinned'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_tracker_comments_is_pinned', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_is_resolved', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_created_at', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_parent_comment_id', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_comment_type', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_user_id', table_name='tracker_comments')
    op.drop_index('ix_tracker_comments_tracker_id', table_name='tracker_comments')
    
    # Drop table
    op.execute("DROP TABLE IF EXISTS tracker_comments")
    
    # Drop enum type (but don't fail if it doesn't exist)
    op.execute("DROP TYPE IF EXISTS commenttype")