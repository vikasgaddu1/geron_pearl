"""add use_cases to reporting_efforts

Revision ID: 404a7ba0700b
Revises: 7f831353c22a
Create Date: 2026-01-06 17:19:59.949556

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '404a7ba0700b'
down_revision = '7f831353c22a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add use_cases array column to reporting_efforts
    op.add_column('reporting_efforts', sa.Column('use_cases', postgresql.ARRAY(sa.String(length=50)), nullable=True))


def downgrade() -> None:
    op.drop_column('reporting_efforts', 'use_cases')
