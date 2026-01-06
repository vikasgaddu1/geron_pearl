"""Add milestone tracking tables (phases and milestones)

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'add_ig_versions'  # Chain after ig_versions migration
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
    # Create reporting_effort_phases table if it doesn't exist
    if not table_exists('reporting_effort_phases'):
        op.create_table(
            'reporting_effort_phases',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('reporting_effort_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['reporting_effort_id'], ['reporting_efforts.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for phases
        op.create_index('ix_reporting_effort_phases_reporting_effort_id', 'reporting_effort_phases', ['reporting_effort_id'])
        op.create_index('ix_reporting_effort_phases_display_order', 'reporting_effort_phases', ['display_order'])
    else:
        # Create indexes if they don't exist
        if not index_exists('reporting_effort_phases', 'ix_reporting_effort_phases_reporting_effort_id'):
            op.create_index('ix_reporting_effort_phases_reporting_effort_id', 'reporting_effort_phases', ['reporting_effort_id'])
        if not index_exists('reporting_effort_phases', 'ix_reporting_effort_phases_display_order'):
            op.create_index('ix_reporting_effort_phases_display_order', 'reporting_effort_phases', ['display_order'])
    
    # Create reporting_effort_milestones table if it doesn't exist
    if not table_exists('reporting_effort_milestones'):
        op.create_table(
            'reporting_effort_milestones',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('phase_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=500), nullable=False),
            sa.Column('due_date', sa.Date(), nullable=True),
            sa.Column('responsibility', sa.String(length=255), nullable=True),
            sa.Column('comments', sa.Text(), nullable=True),
            sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('completion_date', sa.Date(), nullable=True),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['phase_id'], ['reporting_effort_phases.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for milestones
        op.create_index('ix_reporting_effort_milestones_phase_id', 'reporting_effort_milestones', ['phase_id'])
        op.create_index('ix_reporting_effort_milestones_due_date', 'reporting_effort_milestones', ['due_date'])
        op.create_index('ix_reporting_effort_milestones_is_completed', 'reporting_effort_milestones', ['is_completed'])
        op.create_index('ix_reporting_effort_milestones_display_order', 'reporting_effort_milestones', ['display_order'])
    else:
        # Create indexes if they don't exist
        if not index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_phase_id'):
            op.create_index('ix_reporting_effort_milestones_phase_id', 'reporting_effort_milestones', ['phase_id'])
        if not index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_due_date'):
            op.create_index('ix_reporting_effort_milestones_due_date', 'reporting_effort_milestones', ['due_date'])
        if not index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_is_completed'):
            op.create_index('ix_reporting_effort_milestones_is_completed', 'reporting_effort_milestones', ['is_completed'])
        if not index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_display_order'):
            op.create_index('ix_reporting_effort_milestones_display_order', 'reporting_effort_milestones', ['display_order'])


def downgrade() -> None:
    # Drop milestones table and indexes
    if table_exists('reporting_effort_milestones'):
        if index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_display_order'):
            op.drop_index('ix_reporting_effort_milestones_display_order', table_name='reporting_effort_milestones')
        if index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_is_completed'):
            op.drop_index('ix_reporting_effort_milestones_is_completed', table_name='reporting_effort_milestones')
        if index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_due_date'):
            op.drop_index('ix_reporting_effort_milestones_due_date', table_name='reporting_effort_milestones')
        if index_exists('reporting_effort_milestones', 'ix_reporting_effort_milestones_phase_id'):
            op.drop_index('ix_reporting_effort_milestones_phase_id', table_name='reporting_effort_milestones')
        op.drop_table('reporting_effort_milestones')
    
    # Drop phases table and indexes
    if table_exists('reporting_effort_phases'):
        if index_exists('reporting_effort_phases', 'ix_reporting_effort_phases_display_order'):
            op.drop_index('ix_reporting_effort_phases_display_order', table_name='reporting_effort_phases')
        if index_exists('reporting_effort_phases', 'ix_reporting_effort_phases_reporting_effort_id'):
            op.drop_index('ix_reporting_effort_phases_reporting_effort_id', table_name='reporting_effort_phases')
        op.drop_table('reporting_effort_phases')

