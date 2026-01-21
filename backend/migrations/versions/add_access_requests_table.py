"""Add access_requests table for role/access requests

Revision ID: g8h9i0j1k2l3
Revises: f7g8h9i0j1k2
Create Date: 2026-01-15 14:00:00.000000

This migration:
1. Creates the access_requests table for users to request EDITOR or RESPONSIBLE_USER access
2. Creates necessary indexes for efficient querying
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'g8h9i0j1k2l3'
down_revision = 'f7g8h9i0j1k2'
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade() -> None:
    # Create access_requests table if it doesn't exist
    if not table_exists('access_requests'):
        op.create_table(
            'access_requests',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            # Requester info
            sa.Column('requester_id', sa.Integer(), nullable=False),
            # Study info
            sa.Column('study_id', sa.Integer(), nullable=False),
            # Request details
            sa.Column('request_type', sa.String(50), nullable=False),  # EDITOR or RESPONSIBLE_USER
            sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),  # PENDING, APPROVED, DENIED
            sa.Column('request_reason', sa.Text(), nullable=True),
            # Resolution details
            sa.Column('resolved_by_id', sa.Integer(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('denial_reason', sa.Text(), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            # Foreign keys
            sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes for common queries
        op.create_index('ix_access_requests_requester_id', 'access_requests', ['requester_id'])
        op.create_index('ix_access_requests_study_id', 'access_requests', ['study_id'])
        op.create_index('ix_access_requests_status', 'access_requests', ['status'])
        op.create_index('ix_access_requests_status_created', 'access_requests', ['status', 'created_at'])


def downgrade() -> None:
    if table_exists('access_requests'):
        # Drop indexes
        if index_exists('access_requests', 'ix_access_requests_status_created'):
            op.drop_index('ix_access_requests_status_created', table_name='access_requests')
        if index_exists('access_requests', 'ix_access_requests_status'):
            op.drop_index('ix_access_requests_status', table_name='access_requests')
        if index_exists('access_requests', 'ix_access_requests_study_id'):
            op.drop_index('ix_access_requests_study_id', table_name='access_requests')
        if index_exists('access_requests', 'ix_access_requests_requester_id'):
            op.drop_index('ix_access_requests_requester_id', table_name='access_requests')

        # Drop table
        op.drop_table('access_requests')
