"""Create item_completion_records table for velocity tracking

Revision ID: add_item_completion_records
Revises: add_complexity_to_tracker
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_item_completion_records'
down_revision = 'add_complexity_to_tracker'
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
    """Create item_completion_records table."""
    if not table_exists('item_completion_records'):
        op.create_table(
            'item_completion_records',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('tracker_id', sa.Integer(), nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('item_subtype', sa.String(50), nullable=False),
            sa.Column('complexity', sa.Integer(), nullable=False),
            sa.Column('production_programmer_id', sa.Integer(), nullable=False),
            sa.Column('programmer_experience_level', sa.String(20), nullable=False),
            sa.Column('programmer_allocation_percent', sa.Integer(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=False),
            sa.Column('iso_week', sa.Integer(), nullable=False),
            sa.Column('iso_year', sa.Integer(), nullable=False),
            sa.Column('had_sister_study', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('sister_study_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['tracker_id'], ['reporting_effort_item_tracker.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['production_programmer_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for efficient querying
        op.create_index('ix_item_completion_records_tracker_id', 'item_completion_records', ['tracker_id'])
        op.create_index('ix_item_completion_records_study_id', 'item_completion_records', ['study_id'])
        op.create_index('ix_item_completion_records_programmer_id', 'item_completion_records', ['production_programmer_id'])
        op.create_index('ix_item_completion_records_completed_at', 'item_completion_records', ['completed_at'])
        op.create_index('ix_item_completion_records_iso_week_year', 'item_completion_records', ['iso_year', 'iso_week'])
        
        print("Created item_completion_records table")
    else:
        print("item_completion_records table already exists, skipping")


def downgrade() -> None:
    """Drop item_completion_records table."""
    if table_exists('item_completion_records'):
        # Drop indexes first
        if index_exists('item_completion_records', 'ix_item_completion_records_iso_week_year'):
            op.drop_index('ix_item_completion_records_iso_week_year', table_name='item_completion_records')
        if index_exists('item_completion_records', 'ix_item_completion_records_completed_at'):
            op.drop_index('ix_item_completion_records_completed_at', table_name='item_completion_records')
        if index_exists('item_completion_records', 'ix_item_completion_records_programmer_id'):
            op.drop_index('ix_item_completion_records_programmer_id', table_name='item_completion_records')
        if index_exists('item_completion_records', 'ix_item_completion_records_study_id'):
            op.drop_index('ix_item_completion_records_study_id', table_name='item_completion_records')
        if index_exists('item_completion_records', 'ix_item_completion_records_tracker_id'):
            op.drop_index('ix_item_completion_records_tracker_id', table_name='item_completion_records')
        
        op.drop_table('item_completion_records')

