"""Repair migration - safely add any columns that may be missing.

This migration uses IF NOT EXISTS / checks to be idempotent.
It can be safely run on databases that already have these columns.

Revision ID: repair_missing_columns
Revises: 6a0647ea9abd
Create Date: 2026-01-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'repair_missing_columns'
down_revision = '6a0647ea9abd'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add any missing columns that should exist based on current models."""
    
    # database_releases.database_release_date
    if not column_exists('database_releases', 'database_release_date'):
        op.add_column('database_releases', 
                      sa.Column('database_release_date', sa.String(50), nullable=True))
        print("Added database_releases.database_release_date")
    
    # Add any other potentially missing columns here
    # Each check is idempotent - safe to run multiple times


def downgrade() -> None:
    # This is a repair migration, downgrade is a no-op
    pass

