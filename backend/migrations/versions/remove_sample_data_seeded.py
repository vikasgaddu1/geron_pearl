"""Remove sample_data_seeded column from tenants

Revision ID: remove_sample_data_seeded
Revises: add_tracker_items_limit
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_sample_data_seeded'
down_revision = 'add_tracker_items_limit'
branch_labels = None
depends_on = None


def upgrade():
    # Remove sample_data_seeded column from tenants table
    op.drop_column('tenants', 'sample_data_seeded')


def downgrade():
    # Re-add sample_data_seeded column to tenants table
    op.add_column('tenants',
        sa.Column('sample_data_seeded', sa.Boolean(), nullable=False, server_default='false')
    )
