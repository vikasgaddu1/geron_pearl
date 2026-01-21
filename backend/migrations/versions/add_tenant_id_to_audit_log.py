"""Add tenant_id column to audit_log table for multi-tenancy support

Revision ID: e6f7g8h9i0j1
Revises: d5e6f7g8h9i0
Create Date: 2026-01-13 10:00:00.000000

This migration adds a tenant_id column to the audit_log table to support
multi-tenant deployments. Each PEARL instance can be configured with a
tenant_id, and all audit entries will be tagged with that identifier.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'e6f7g8h9i0j1'
down_revision = 'd5e6f7g8h9i0'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Add tenant_id column to audit_log table if it doesn't exist
    if not column_exists('audit_log', 'tenant_id'):
        op.add_column(
            'audit_log',
            sa.Column('tenant_id', sa.String(100), nullable=True)
        )

    # Create index on tenant_id for efficient queries
    if not index_exists('audit_log', 'ix_audit_log_tenant_id'):
        op.create_index(
            'ix_audit_log_tenant_id',
            'audit_log',
            ['tenant_id']
        )


def downgrade() -> None:
    # Drop index first
    if index_exists('audit_log', 'ix_audit_log_tenant_id'):
        op.drop_index('ix_audit_log_tenant_id', table_name='audit_log')

    # Drop column
    if column_exists('audit_log', 'tenant_id'):
        op.drop_column('audit_log', 'tenant_id')
