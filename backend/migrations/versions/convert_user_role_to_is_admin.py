"""Convert user role enum to is_admin boolean.

Revision ID: convert_role_to_is_admin
Revises: c4d5e6f7g8h9
Create Date: 2025-01-05
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'convert_role_to_is_admin'
down_revision = 'c4d5e6f7g8h9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add is_admin column (defaults to False)
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True))
    
    # 2. Migrate existing data: ADMIN role -> is_admin=True, others -> is_admin=False
    op.execute("""
        UPDATE users 
        SET is_admin = CASE 
            WHEN role = 'ADMIN' THEN TRUE 
            ELSE FALSE 
        END
    """)
    
    # 3. Make is_admin NOT NULL after data migration
    op.alter_column('users', 'is_admin', nullable=False, server_default='false')
    
    # 4. Drop the old role column
    op.drop_column('users', 'role')


def downgrade() -> None:
    # 1. Re-create the role enum type
    role_enum = sa.Enum('ADMIN', 'EDITOR', 'VIEWER', name='userrole')
    
    # 2. Add the role column back
    op.add_column('users', sa.Column('role', role_enum, nullable=True))
    
    # 3. Migrate data back: is_admin=True -> ADMIN, is_admin=False -> VIEWER (default)
    op.execute("""
        UPDATE users 
        SET role = CASE 
            WHEN is_admin = TRUE THEN 'ADMIN' 
            ELSE 'VIEWER' 
        END
    """)
    
    # 4. Make role NOT NULL
    op.alter_column('users', 'role', nullable=False)
    
    # 5. Drop is_admin column
    op.drop_column('users', 'is_admin')

