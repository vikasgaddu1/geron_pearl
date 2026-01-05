"""add tracker_status_history table

Revision ID: add_status_history
Revises: add_ready_for_qc
Create Date: 2026-01-05

Adds the tracker_status_history table for tracking time spent in each status.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_status_history'
down_revision = 'add_ready_for_qc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tracker_status_history table
    op.create_table(
        'tracker_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('status_field', sa.String(length=20), nullable=False),
        sa.Column('status_value', sa.String(length=50), nullable=False),
        sa.Column('entered_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('exited_at', sa.DateTime(), nullable=True),
        sa.Column('changed_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['tracker_id'], 
            ['reporting_effort_item_tracker.id'], 
            ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['changed_by_user_id'], 
            ['users.id'], 
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(
        'ix_tracker_status_history_tracker_id', 
        'tracker_status_history', 
        ['tracker_id'], 
        unique=False
    )
    op.create_index(
        'ix_tracker_status_history_tracker_field', 
        'tracker_status_history', 
        ['tracker_id', 'status_field'], 
        unique=False
    )
    op.create_index(
        'ix_tracker_status_history_entered_at', 
        'tracker_status_history', 
        ['entered_at'], 
        unique=False
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_tracker_status_history_entered_at', table_name='tracker_status_history')
    op.drop_index('ix_tracker_status_history_tracker_field', table_name='tracker_status_history')
    op.drop_index('ix_tracker_status_history_tracker_id', table_name='tracker_status_history')
    
    # Drop table
    op.drop_table('tracker_status_history')

