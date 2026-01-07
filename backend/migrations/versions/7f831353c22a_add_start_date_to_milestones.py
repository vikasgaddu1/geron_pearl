"""add start_date to milestones

Revision ID: 7f831353c22a
Revises: ee7684fa608b
Create Date: 2026-01-06 17:05:40.649194

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f831353c22a'
down_revision = 'ee7684fa608b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add start_date column to reporting_effort_milestones
    op.add_column('reporting_effort_milestones', sa.Column('start_date', sa.Date(), nullable=True))
    op.create_index(op.f('ix_reporting_effort_milestones_start_date'), 'reporting_effort_milestones', ['start_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reporting_effort_milestones_start_date'), table_name='reporting_effort_milestones')
    op.drop_column('reporting_effort_milestones', 'start_date')
