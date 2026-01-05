"""add ready_for_qc production status

Revision ID: add_ready_for_qc
Revises: add_comment_type_to_tracker_comments
Create Date: 2026-01-05

This migration documents the addition of the 'ready_for_qc' value 
to the production_status field. Since production_status is a String 
column (not a PostgreSQL ENUM), no schema change is required.

The new valid values for production_status are:
- not_started
- in_progress
- ready_for_qc (NEW)
- completed
- on_hold

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ready_for_qc'
down_revision = 'add_comment_type_to_tracker_comments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # production_status is a String column, so no schema change needed
    # This migration documents the addition of 'ready_for_qc' as a valid value
    # The validation is enforced at the application level via the ProductionStatus enum
    pass


def downgrade() -> None:
    # If downgrading, update any 'ready_for_qc' values to 'in_progress'
    # to maintain data consistency
    op.execute("""
        UPDATE reporting_effort_item_tracker 
        SET production_status = 'in_progress' 
        WHERE production_status = 'ready_for_qc'
    """)

