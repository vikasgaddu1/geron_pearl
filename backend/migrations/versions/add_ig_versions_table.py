"""Add IG versions table and ig_version_id to dataset details

Revision ID: add_ig_versions
Revises: 
Create Date: 2026-01-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_ig_versions'
down_revision = 'c3d4e5f6g7h8'  # Points to add_item_description migration
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


def upgrade() -> None:
    # Create ig_versions table if it doesn't exist
    if not table_exists('ig_versions'):
        op.create_table(
            'ig_versions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('standard_type', sa.String(length=10), nullable=False),
            sa.Column('version', sa.String(length=20), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('standard_type', 'version', name='uq_ig_version_standard_version')
        )
        
        # Insert default SDTM versions
        op.execute("""
            INSERT INTO ig_versions (standard_type, version, description, is_active) VALUES 
            ('SDTM', '3.2', 'SDTM Implementation Guide v3.2', true),
            ('SDTM', '3.3', 'SDTM Implementation Guide v3.3', true),
            ('SDTM', '3.4', 'SDTM Implementation Guide v3.4', true)
        """)
        
        # Insert default ADaM versions
        op.execute("""
            INSERT INTO ig_versions (standard_type, version, description, is_active) VALUES 
            ('ADaM', '1.1', 'ADaM Implementation Guide v1.1', true),
            ('ADaM', '1.2', 'ADaM Implementation Guide v1.2', true),
            ('ADaM', '1.3', 'ADaM Implementation Guide v1.3', true)
        """)
    
    # Create index on ig_versions if it doesn't exist
    if not index_exists('ig_versions', 'ix_ig_versions_standard_type'):
        op.create_index('ix_ig_versions_standard_type', 'ig_versions', ['standard_type'])
    
    # Add ig_version_id column to reporting_effort_dataset_details if it doesn't exist
    if not column_exists('reporting_effort_dataset_details', 'ig_version_id'):
        op.add_column(
            'reporting_effort_dataset_details',
            sa.Column('ig_version_id', sa.Integer(), nullable=True)
        )
        op.create_foreign_key(
            'fk_dataset_details_ig_version',
            'reporting_effort_dataset_details',
            'ig_versions',
            ['ig_version_id'],
            ['id']
        )
        op.create_index(
            'ix_dataset_details_ig_version_id',
            'reporting_effort_dataset_details',
            ['ig_version_id']
        )


def downgrade() -> None:
    # Remove foreign key and column from reporting_effort_dataset_details
    if column_exists('reporting_effort_dataset_details', 'ig_version_id'):
        if index_exists('reporting_effort_dataset_details', 'ix_dataset_details_ig_version_id'):
            op.drop_index('ix_dataset_details_ig_version_id', table_name='reporting_effort_dataset_details')
        op.drop_constraint('fk_dataset_details_ig_version', 'reporting_effort_dataset_details', type_='foreignkey')
        op.drop_column('reporting_effort_dataset_details', 'ig_version_id')
    
    # Drop ig_versions table
    if table_exists('ig_versions'):
        if index_exists('ig_versions', 'ix_ig_versions_standard_type'):
            op.drop_index('ix_ig_versions_standard_type', table_name='ig_versions')
        op.drop_table('ig_versions')

