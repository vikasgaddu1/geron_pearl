"""Add database_release_date column to database_releases table.

Revision ID: add_database_release_date
Revises: df7267a2f25d
Create Date: 2026-01-06
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_database_release_date'
down_revision = 'df7267a2f25d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('database_releases', sa.Column('database_release_date', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('database_releases', 'database_release_date')





