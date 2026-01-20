"""Add tenant onboarding fields

Revision ID: add_tenant_onboarding
Revises: add_rls_policies
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_tenant_onboarding'
down_revision: Union[str, None] = 'add_rls_policies'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add onboarding_completed and sample_data_seeded columns to tenants,
    and remove duplicate columns from tenant_settings.
    """
    # Add onboarding_completed column to tenants
    op.add_column(
        'tenants',
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True)
    )
    
    # Add sample_data_seeded column to tenants
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
    
    # Remove duplicate columns from tenant_settings (they were incorrectly placed there)
    # These columns now live on the tenants table
    op.drop_column('tenant_settings', 'onboarding_completed')
    op.drop_column('tenant_settings', 'sample_data_active')


def downgrade() -> None:
    """Remove onboarding fields from tenants and restore to tenant_settings."""
    # Restore columns to tenant_settings
    op.add_column(
        'tenant_settings',
        sa.Column('onboarding_completed', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'tenant_settings',
        sa.Column('sample_data_active', sa.Integer(), nullable=False, server_default='1')
    )
    
    # Remove columns from tenants
    op.drop_column('tenants', 'sample_data_seeded')
    op.drop_column('tenants', 'onboarding_completed')
