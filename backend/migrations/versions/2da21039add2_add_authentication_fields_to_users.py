"""add_authentication_fields_to_users

Revision ID: 2da21039add2
Revises: 29fb258b890f
Create Date: 2025-12-22 19:30:01.043547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2da21039add2'
down_revision = '29fb258b890f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email column
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Add password_hash column
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))
    
    # Create auth_provider enum type
    op.execute("CREATE TYPE authprovider AS ENUM ('local', 'google', 'microsoft', 'github', 'okta', 'custom')")
    op.add_column('users', sa.Column('auth_provider', sa.Enum('local', 'google', 'microsoft', 'github', 'okta', 'custom', name='authprovider'), nullable=False, server_default='local'))
    
    # Add auth_provider_id column
    op.add_column('users', sa.Column('auth_provider_id', sa.String(), nullable=True))
    
    # Add is_active column
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add last_login_at column
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    
    # Add password reset columns
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove password reset columns
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
    
    # Remove authentication columns
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'auth_provider_id')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'password_hash')
    
    # Remove email column
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'email')
    
    # Drop auth_provider enum type
    op.execute("DROP TYPE authprovider")