"""Add biostat review workflow for TLF items

Revision ID: add_biostat_review
Revises: 5313a64fa725
Create Date: 2026-01-21 12:00:00.000000

This migration:
1. Adds biostat_status, biostat_reviewer_id, biostat_review_date to tracker
2. Adds unresolved_biostat_comment_count to tracker
3. Creates study_default_biostats table
4. Creates necessary indexes
5. Migrates existing data (grandfathers completed TLF items)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_biostat_review'
down_revision = '5313a64fa725'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """Check if a unique constraint exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def upgrade() -> None:
    # Step 1: Add biostat columns to reporting_effort_item_tracker
    if not column_exists('reporting_effort_item_tracker', 'biostat_status'):
        op.add_column(
            'reporting_effort_item_tracker',
            sa.Column('biostat_status', sa.String(50), nullable=False, server_default='not_applicable')
        )
        op.create_index(
            'ix_tracker_biostat_status',
            'reporting_effort_item_tracker',
            ['biostat_status']
        )

    if not column_exists('reporting_effort_item_tracker', 'biostat_reviewer_id'):
        op.add_column(
            'reporting_effort_item_tracker',
            sa.Column('biostat_reviewer_id', sa.Integer(), nullable=True)
        )
        op.create_foreign_key(
            'fk_tracker_biostat_reviewer',
            'reporting_effort_item_tracker',
            'users',
            ['biostat_reviewer_id'],
            ['id']
        )
        op.create_index(
            'ix_tracker_biostat_reviewer_id',
            'reporting_effort_item_tracker',
            ['biostat_reviewer_id']
        )

    if not column_exists('reporting_effort_item_tracker', 'biostat_review_date'):
        op.add_column(
            'reporting_effort_item_tracker',
            sa.Column('biostat_review_date', sa.Date(), nullable=True)
        )

    if not column_exists('reporting_effort_item_tracker', 'unresolved_biostat_comment_count'):
        op.add_column(
            'reporting_effort_item_tracker',
            sa.Column('unresolved_biostat_comment_count', sa.Integer(), nullable=False, server_default='0')
        )
        op.create_index(
            'ix_tracker_unresolved_biostat_count',
            'reporting_effort_item_tracker',
            ['unresolved_biostat_comment_count']
        )

    # Step 2: Create study_default_biostats table
    if not table_exists('study_default_biostats'):
        op.create_table(
            'study_default_biostats',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_study_default_biostats_study_id', 'study_default_biostats', ['study_id'])
        op.create_index('ix_study_default_biostats_user_id', 'study_default_biostats', ['user_id'])
        op.create_unique_constraint('uq_study_default_biostat', 'study_default_biostats', ['study_id', 'user_id'])

    # Step 3: Migrate existing data
    # For TLF items with in_production_flag=true (already complete), set biostat_status='passed'
    # For TLF items with qc_status='completed' but in_production_flag=false, set biostat_status='pending'
    # All others remain 'not_applicable'
    op.execute("""
        UPDATE reporting_effort_item_tracker t
        SET biostat_status = 'passed'
        FROM reporting_effort_items i
        WHERE t.reporting_effort_item_id = i.id
          AND i.item_type = 'TLF'
          AND t.qc_status = 'completed'
          AND t.in_production_flag = true
    """)

    op.execute("""
        UPDATE reporting_effort_item_tracker t
        SET biostat_status = 'pending'
        FROM reporting_effort_items i
        WHERE t.reporting_effort_item_id = i.id
          AND i.item_type = 'TLF'
          AND t.qc_status = 'completed'
          AND t.in_production_flag = false
          AND t.biostat_status = 'not_applicable'
    """)


def downgrade() -> None:
    # Step 1: Drop study_default_biostats table
    if table_exists('study_default_biostats'):
        if constraint_exists('study_default_biostats', 'uq_study_default_biostat'):
            op.drop_constraint('uq_study_default_biostat', 'study_default_biostats', type_='unique')
        if index_exists('study_default_biostats', 'ix_study_default_biostats_user_id'):
            op.drop_index('ix_study_default_biostats_user_id', table_name='study_default_biostats')
        if index_exists('study_default_biostats', 'ix_study_default_biostats_study_id'):
            op.drop_index('ix_study_default_biostats_study_id', table_name='study_default_biostats')
        op.drop_table('study_default_biostats')

    # Step 2: Drop biostat columns from reporting_effort_item_tracker
    if column_exists('reporting_effort_item_tracker', 'unresolved_biostat_comment_count'):
        if index_exists('reporting_effort_item_tracker', 'ix_tracker_unresolved_biostat_count'):
            op.drop_index('ix_tracker_unresolved_biostat_count', table_name='reporting_effort_item_tracker')
        op.drop_column('reporting_effort_item_tracker', 'unresolved_biostat_comment_count')

    if column_exists('reporting_effort_item_tracker', 'biostat_review_date'):
        op.drop_column('reporting_effort_item_tracker', 'biostat_review_date')

    if column_exists('reporting_effort_item_tracker', 'biostat_reviewer_id'):
        if index_exists('reporting_effort_item_tracker', 'ix_tracker_biostat_reviewer_id'):
            op.drop_index('ix_tracker_biostat_reviewer_id', table_name='reporting_effort_item_tracker')
        op.drop_constraint('fk_tracker_biostat_reviewer', 'reporting_effort_item_tracker', type_='foreignkey')
        op.drop_column('reporting_effort_item_tracker', 'biostat_reviewer_id')

    if column_exists('reporting_effort_item_tracker', 'biostat_status'):
        if index_exists('reporting_effort_item_tracker', 'ix_tracker_biostat_status'):
            op.drop_index('ix_tracker_biostat_status', table_name='reporting_effort_item_tracker')
        op.drop_column('reporting_effort_item_tracker', 'biostat_status')
