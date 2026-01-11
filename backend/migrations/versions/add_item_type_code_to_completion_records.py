"""Add item_type and item_code columns to item_completion_records

Revision ID: add_item_type_code_completion
Revises: add_item_completion_records
Create Date: 2026-01-11

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_item_type_code_completion'
down_revision = 'add_item_completion_records'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add item_type and item_code columns to item_completion_records."""
    
    # Add item_type column if it doesn't exist
    if not column_exists('item_completion_records', 'item_type'):
        op.add_column(
            'item_completion_records',
            sa.Column('item_type', sa.String(50), nullable=True)
        )
        # Set default value for existing rows
        op.execute("UPDATE item_completion_records SET item_type = 'TLF' WHERE item_type IS NULL")
        # Make column not nullable after setting defaults
        op.alter_column('item_completion_records', 'item_type', nullable=False)
        print("Added item_type column to item_completion_records")
    else:
        print("item_type column already exists, skipping")
    
    # Add item_code column if it doesn't exist
    if not column_exists('item_completion_records', 'item_code'):
        op.add_column(
            'item_completion_records',
            sa.Column('item_code', sa.String(255), nullable=True)
        )
        # Set default value for existing rows
        op.execute("UPDATE item_completion_records SET item_code = 'UNKNOWN' WHERE item_code IS NULL")
        # Make column not nullable after setting defaults
        op.alter_column('item_completion_records', 'item_code', nullable=False)
        print("Added item_code column to item_completion_records")
    else:
        print("item_code column already exists, skipping")


def downgrade() -> None:
    """Remove item_type and item_code columns from item_completion_records."""
    if column_exists('item_completion_records', 'item_code'):
        op.drop_column('item_completion_records', 'item_code')
    
    if column_exists('item_completion_records', 'item_type'):
        op.drop_column('item_completion_records', 'item_type')
