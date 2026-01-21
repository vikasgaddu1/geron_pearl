"""Make email required for authentication

Revision ID: f7g8h9i0j1k2
Revises: e6f7g8h9i0j1
Create Date: 2026-01-15 12:00:00.000000

This migration:
1. Updates users with NULL email to placeholder: {username}@placeholder.pearl.local
2. Makes the email column NOT NULL (required for email-based authentication)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'f7g8h9i0j1k2'
down_revision = 'e6f7g8h9i0j1'
branch_labels = None
depends_on = None


def column_is_nullable(table_name: str, column_name: str) -> bool:
    """Check if a column is nullable."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {col['name']: col for col in inspector.get_columns(table_name)}
    if column_name in columns:
        return columns[column_name].get('nullable', True)
    return True


def upgrade() -> None:
    # Step 1: Update any NULL emails to placeholder values
    # Using raw SQL for compatibility with both PostgreSQL and SQLite
    # Note: Using .example.com as it's a valid reserved domain for examples
    op.execute(
        sa.text("""
            UPDATE users
            SET email = username || '@placeholder.example.com'
            WHERE email IS NULL
        """)
    )

    # Step 2: Alter column to NOT NULL
    # Only if not already NOT NULL
    if column_is_nullable('users', 'email'):
        op.alter_column(
            'users',
            'email',
            existing_type=sa.String(),
            nullable=False
        )


def downgrade() -> None:
    # Allow NULL emails again
    if not column_is_nullable('users', 'email'):
        op.alter_column(
            'users',
            'email',
            existing_type=sa.String(),
            nullable=True
        )
