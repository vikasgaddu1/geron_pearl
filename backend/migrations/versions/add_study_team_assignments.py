"""Create study_team_assignments table for resource allocation tracking

Revision ID: add_study_team_assignments
Revises: repair_missing_columns
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_study_team_assignments'
down_revision = 'repair_missing_columns'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    """Create study_team_assignments table."""
    if not table_exists('study_team_assignments'):
        op.create_table(
            'study_team_assignments',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('job_type', sa.String(50), nullable=False),
            sa.Column('allocation_percentage', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('productive_time_factor', sa.Integer(), nullable=False, server_default='75'),
            sa.Column('experience_level', sa.String(20), nullable=False, server_default='MID'),
            sa.Column('effective_start_date', sa.Date(), nullable=False),
            sa.Column('effective_end_date', sa.Date(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('departure_reason', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for efficient querying
        op.create_index('ix_study_team_assignments_user_id', 'study_team_assignments', ['user_id'])
        op.create_index('ix_study_team_assignments_study_id', 'study_team_assignments', ['study_id'])
        op.create_index('ix_study_team_assignments_is_active', 'study_team_assignments', ['is_active'])
        op.create_index('ix_study_team_assignments_effective_dates', 'study_team_assignments', 
                       ['effective_start_date', 'effective_end_date'])
        
        print("Created study_team_assignments table")
    else:
        print("study_team_assignments table already exists, skipping")


def downgrade() -> None:
    """Drop study_team_assignments table."""
    if table_exists('study_team_assignments'):
        # Drop indexes first
        if index_exists('study_team_assignments', 'ix_study_team_assignments_effective_dates'):
            op.drop_index('ix_study_team_assignments_effective_dates', table_name='study_team_assignments')
        if index_exists('study_team_assignments', 'ix_study_team_assignments_is_active'):
            op.drop_index('ix_study_team_assignments_is_active', table_name='study_team_assignments')
        if index_exists('study_team_assignments', 'ix_study_team_assignments_study_id'):
            op.drop_index('ix_study_team_assignments_study_id', table_name='study_team_assignments')
        if index_exists('study_team_assignments', 'ix_study_team_assignments_user_id'):
            op.drop_index('ix_study_team_assignments_user_id', table_name='study_team_assignments')
        
        op.drop_table('study_team_assignments')

