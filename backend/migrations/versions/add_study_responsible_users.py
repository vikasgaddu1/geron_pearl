"""Add study_responsible_users table to replace LEAD role

Revision ID: d5e6f7g8h9i0
Revises: 12812f1105e7
Create Date: 2026-01-12 20:00:00.000000

This migration:
1. Creates the study_responsible_users table
2. Migrates existing LEAD role assignments to the new table
3. Deletes LEAD entries from user_study_roles

Note: The LEAD value in the studyrole enum is kept for backward compatibility
but will no longer be used by the application.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'd5e6f7g8h9i0'
down_revision = '12812f1105e7'
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


def constraint_exists(table_name: str, constraint_name: str) -> bool:
    """Check if a unique constraint exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def upgrade() -> None:
    # Step 1: Create study_responsible_users table if it doesn't exist
    if not table_exists('study_responsible_users'):
        op.create_table(
            'study_responsible_users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

        # Create indexes
        op.create_index('ix_study_responsible_users_study_id', 'study_responsible_users', ['study_id'])
        op.create_index('ix_study_responsible_users_user_id', 'study_responsible_users', ['user_id'])

        # Create unique constraint for one assignment per user per study
        op.create_unique_constraint('uq_study_responsible_user', 'study_responsible_users', ['user_id', 'study_id'])

    # Step 2: Migrate existing LEAD users to study_responsible_users
    # First LEAD per study becomes is_primary=true
    if table_exists('user_study_roles'):
        # Use raw SQL for the migration to handle the ROW_NUMBER logic
        # This works for PostgreSQL
        op.execute("""
            INSERT INTO study_responsible_users (study_id, user_id, is_primary, created_at, updated_at)
            SELECT
                study_id,
                user_id,
                (rn = 1) as is_primary,
                created_at,
                NOW() as updated_at
            FROM (
                SELECT
                    study_id,
                    user_id,
                    created_at,
                    ROW_NUMBER() OVER (PARTITION BY study_id ORDER BY created_at) as rn
                FROM user_study_roles
                WHERE role = 'LEAD'
            ) sub
            ON CONFLICT (user_id, study_id) DO NOTHING
        """)

        # Step 3: Delete LEAD entries from user_study_roles
        op.execute("DELETE FROM user_study_roles WHERE role = 'LEAD'")


def downgrade() -> None:
    # Step 1: Migrate study_responsible_users back to user_study_roles as LEAD
    if table_exists('study_responsible_users') and table_exists('user_study_roles'):
        op.execute("""
            INSERT INTO user_study_roles (study_id, user_id, role, created_at, updated_at)
            SELECT
                study_id,
                user_id,
                'LEAD' as role,
                created_at,
                NOW() as updated_at
            FROM study_responsible_users
            ON CONFLICT (user_id, study_id) DO NOTHING
        """)

    # Step 2: Drop study_responsible_users table
    if table_exists('study_responsible_users'):
        # Drop indexes
        if index_exists('study_responsible_users', 'ix_study_responsible_users_user_id'):
            op.drop_index('ix_study_responsible_users_user_id', table_name='study_responsible_users')
        if index_exists('study_responsible_users', 'ix_study_responsible_users_study_id'):
            op.drop_index('ix_study_responsible_users_study_id', table_name='study_responsible_users')

        # Drop unique constraint
        if constraint_exists('study_responsible_users', 'uq_study_responsible_user'):
            op.drop_constraint('uq_study_responsible_user', 'study_responsible_users', type_='unique')

        # Drop table
        op.drop_table('study_responsible_users')
