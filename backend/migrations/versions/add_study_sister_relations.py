"""Create study_sister_relations table for code reuse tracking

Revision ID: add_study_sister_relations
Revises: add_item_completion_records
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_study_sister_relations'
down_revision = 'add_item_completion_records'
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


def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """Check if a unique constraint exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def upgrade() -> None:
    """Create study_sister_relations table."""
    if not table_exists('study_sister_relations'):
        op.create_table(
            'study_sister_relations',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('primary_study_id', sa.Integer(), nullable=False),
            sa.Column('sister_study_id', sa.Integer(), nullable=False),
            sa.Column('code_reuse_percentage', sa.Integer(), nullable=False, server_default='50'),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['primary_study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['sister_study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes for efficient querying
        op.create_index('ix_study_sister_relations_primary_study_id', 'study_sister_relations', ['primary_study_id'])
        op.create_index('ix_study_sister_relations_sister_study_id', 'study_sister_relations', ['sister_study_id'])
        
        # Unique constraint: only one relationship per study pair
        op.create_unique_constraint(
            'uq_study_sister_relation_pair',
            'study_sister_relations',
            ['primary_study_id', 'sister_study_id']
        )
        
        print("Created study_sister_relations table")
    else:
        print("study_sister_relations table already exists, skipping")


def downgrade() -> None:
    """Drop study_sister_relations table."""
    if table_exists('study_sister_relations'):
        # Drop constraint first
        if constraint_exists('study_sister_relations', 'uq_study_sister_relation_pair'):
            op.drop_constraint('uq_study_sister_relation_pair', 'study_sister_relations', type_='unique')
        
        # Drop indexes
        if index_exists('study_sister_relations', 'ix_study_sister_relations_sister_study_id'):
            op.drop_index('ix_study_sister_relations_sister_study_id', table_name='study_sister_relations')
        if index_exists('study_sister_relations', 'ix_study_sister_relations_primary_study_id'):
            op.drop_index('ix_study_sister_relations_primary_study_id', table_name='study_sister_relations')
        
        op.drop_table('study_sister_relations')

