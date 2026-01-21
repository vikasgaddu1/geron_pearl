"""Add max_tracker_items to subscription_plans

Revision ID: add_tracker_items_limit
Revises: ebe30a019c99
Create Date: 2026-01-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tracker_items_limit'
down_revision = 'ebe30a019c99'
branch_labels = None
depends_on = None


def upgrade():
    # Add max_tracker_items column to subscription_plans
    op.add_column(
        'subscription_plans',
        sa.Column('max_tracker_items', sa.Integer(), nullable=False, server_default='1000')
    )

    # Update existing plans with appropriate values
    # Starter: 1000, Professional: 10000, Enterprise: -1 (unlimited)
    op.execute("""
        UPDATE subscription_plans
        SET max_tracker_items = CASE
            WHEN name = 'starter' THEN 1000
            WHEN name = 'professional' THEN 10000
            WHEN name = 'enterprise' THEN -1
            ELSE 1000
        END
    """)


def downgrade():
    op.drop_column('subscription_plans', 'max_tracker_items')
