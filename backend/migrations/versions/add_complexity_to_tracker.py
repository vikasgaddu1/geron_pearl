"""Add complexity field to reporting_effort_item_tracker

Revision ID: add_complexity_to_tracker
Revises: add_study_team_assignments
Create Date: 2026-01-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_complexity_to_tracker'
down_revision = 'add_study_team_assignments'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    """Add complexity column to reporting_effort_item_tracker."""
    if not column_exists('reporting_effort_item_tracker', 'complexity'):
        op.add_column(
            'reporting_effort_item_tracker',
            sa.Column('complexity', sa.Integer(), nullable=False, server_default='3')
        )
        print("Added complexity column to reporting_effort_item_tracker")
    else:
        print("complexity column already exists, skipping")


def downgrade() -> None:
    """Remove complexity column from reporting_effort_item_tracker."""
    if column_exists('reporting_effort_item_tracker', 'complexity'):
        op.drop_column('reporting_effort_item_tracker', 'complexity')

