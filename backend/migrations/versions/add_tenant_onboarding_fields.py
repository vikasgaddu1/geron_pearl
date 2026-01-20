"""Add tenant onboarding fields

Revision ID: add_tenant_onboarding
Revises: 
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_tenant_onboarding'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add onboarding_completed and sample_data_seeded columns to tenants."""
    # Add onboarding_completed column
    op.add_column(
        'tenants',
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True)
    )
    
    # Add sample_data_seeded column
    op.add_column(
        'tenants',
        sa.Column('sample_data_seeded', sa.Boolean(), nullable=True)
    )
    
    # Set default values for existing rows
    op.execute("UPDATE tenants SET onboarding_completed = false WHERE onboarding_completed IS NULL")
    op.execute("UPDATE tenants SET sample_data_seeded = false WHERE sample_data_seeded IS NULL")
    
    # Make columns non-nullable
    op.alter_column('tenants', 'onboarding_completed', nullable=False)
    op.alter_column('tenants', 'sample_data_seeded', nullable=False)


def downgrade() -> None:
    """Remove onboarding fields from tenants."""
    op.drop_column('tenants', 'sample_data_seeded')
    op.drop_column('tenants', 'onboarding_completed')
