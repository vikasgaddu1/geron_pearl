"""Add signature_locks_effort setting to tenant_settings

Revision ID: add_signature_locks_effort
Revises: add_electronic_signature
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_signature_locks_effort'
down_revision = 'add_electronic_signature'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add signature_locks_effort column to tenant_settings
    # Default True means signing automatically locks (new behavior)
    op.add_column('tenant_settings', sa.Column(
        'signature_locks_effort',
        sa.Boolean(),
        nullable=False,
        server_default='true',
        comment='When True, signing automatically locks effort. When False, lock/unlock is manual.'
    ))


def downgrade() -> None:
    op.drop_column('tenant_settings', 'signature_locks_effort')
