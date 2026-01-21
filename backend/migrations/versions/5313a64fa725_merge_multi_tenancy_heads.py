"""merge_multi_tenancy_heads

Revision ID: 5313a64fa725
Revises: add_is_popular_column, add_tenant_onboarding
Create Date: 2026-01-21 08:46:13.846991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5313a64fa725'
down_revision = ('add_is_popular_column', 'add_tenant_onboarding')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass