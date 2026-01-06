"""Add user_study_roles table for study-scoped access control

Revision ID: c4d5e6f7g8h9
Revises: b2c3d4e5f6g7
Create Date: 2026-01-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'c4d5e6f7g8h9'
down_revision = 'b2c3d4e5f6g7'  # Chain after milestone tracking migration
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
    """Check if a constraint exists on a table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def upgrade() -> None:
    # Create study_role enum type
    study_role_enum = sa.Enum('VIEWER', 'EDITOR', 'LEAD', name='studyrole')
    
    # Create user_study_roles table if it doesn't exist
    if not table_exists('user_study_roles'):
        op.create_table(
            'user_study_roles',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('study_id', sa.Integer(), nullable=False),
            sa.Column('role', study_role_enum, nullable=False, server_default='VIEWER'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_user_study_roles_user_id', 'user_study_roles', ['user_id'])
        op.create_index('ix_user_study_roles_study_id', 'user_study_roles', ['study_id'])
        op.create_index('ix_user_study_roles_role', 'user_study_roles', ['role'])
        
        # Create unique constraint for one role per user per study
        op.create_unique_constraint('uq_user_study_role', 'user_study_roles', ['user_id', 'study_id'])
    else:
        # Create indexes if they don't exist
        if not index_exists('user_study_roles', 'ix_user_study_roles_user_id'):
            op.create_index('ix_user_study_roles_user_id', 'user_study_roles', ['user_id'])
        if not index_exists('user_study_roles', 'ix_user_study_roles_study_id'):
            op.create_index('ix_user_study_roles_study_id', 'user_study_roles', ['study_id'])
        if not index_exists('user_study_roles', 'ix_user_study_roles_role'):
            op.create_index('ix_user_study_roles_role', 'user_study_roles', ['role'])


def downgrade() -> None:
    if table_exists('user_study_roles'):
        # Drop indexes
        if index_exists('user_study_roles', 'ix_user_study_roles_role'):
            op.drop_index('ix_user_study_roles_role', table_name='user_study_roles')
        if index_exists('user_study_roles', 'ix_user_study_roles_study_id'):
            op.drop_index('ix_user_study_roles_study_id', table_name='user_study_roles')
        if index_exists('user_study_roles', 'ix_user_study_roles_user_id'):
            op.drop_index('ix_user_study_roles_user_id', table_name='user_study_roles')
        
        # Drop table
        op.drop_table('user_study_roles')
    
    # Drop enum type
    sa.Enum(name='studyrole').drop(op.get_bind(), checkfirst=True)

