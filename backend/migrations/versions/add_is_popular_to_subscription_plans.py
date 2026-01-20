"""Add is_popular column to subscription_plans.

Revision ID: add_is_popular_column
Revises: add_rls_policies
Create Date: 2026-01-20
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_is_popular_column'
down_revision = 'add_rls_policies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_popular column with default False
    op.add_column(
        'subscription_plans',
        sa.Column('is_popular', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Set professional plan as popular by default
    op.execute("""
        UPDATE subscription_plans 
        SET is_popular = true 
        WHERE name = 'professional'
    """)


def downgrade() -> None:
    op.drop_column('subscription_plans', 'is_popular')
