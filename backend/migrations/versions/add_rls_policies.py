"""Add Row-Level Security policies for multi-tenancy.

This migration:
1. Enables RLS on all tenant-aware tables
2. Creates isolation policies using app.current_tenant_id session variable
3. Creates BYPASSRLS role for super admin operations
4. Adds tenant_id to notifications and app_settings tables

Revision ID: add_rls_policies
Revises: add_multi_tenancy_foundation
Create Date: 2026-01-20
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_rls_policies'
down_revision = 'add_multi_tenancy_foundation'
branch_labels = None
depends_on = None


# Tables that need RLS (root entities with tenant_id)
RLS_TABLES = [
    'users',
    'studies',
    'packages',
    'text_elements',
    'audit_log',
    'error_log',
    'notifications',
    'app_settings',
]


def upgrade() -> None:
    # ==========================================
    # Step 1: Add tenant_id to missing tables
    # ==========================================
    
    # Add tenant_id to notifications table
    op.add_column('notifications', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE notifications SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('notifications', 'tenant_id', nullable=False)
    op.create_foreign_key(
        'fk_notifications_tenant', 
        'notifications', 
        'tenants', 
        ['tenant_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_notifications_tenant_user', 'notifications', ['tenant_id', 'user_id'])
    
    # Add tenant_id to app_settings table
    op.add_column('app_settings', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE app_settings SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('app_settings', 'tenant_id', nullable=False)
    op.create_foreign_key(
        'fk_app_settings_tenant',
        'app_settings',
        'tenants',
        ['tenant_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index('ix_app_settings_tenant', 'app_settings', ['tenant_id'])
    
    # ==========================================
    # Step 2: Fix username uniqueness (per-tenant)
    # ==========================================
    
    # Drop global unique constraint on username
    op.drop_constraint('users_username_key', 'users', type_='unique')
    
    # Add per-tenant unique constraint
    op.create_unique_constraint(
        'uq_users_tenant_username',
        'users',
        ['tenant_id', 'username']
    )
    
    # ==========================================
    # Step 3: Assign default plan to default tenant
    # ==========================================
    
    # Get the professional plan ID (or first available plan)
    op.execute("""
        UPDATE tenants 
        SET plan_id = (SELECT id FROM subscription_plans WHERE name = 'professional' LIMIT 1)
        WHERE id = 1 AND plan_id IS NULL
    """)
    
    # ==========================================
    # Step 4: Create BYPASSRLS role for super admin
    # ==========================================
    
    # Note: This creates the role if it doesn't exist
    # The password should be set via ALTER ROLE after deployment
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pearl_super_admin') THEN
                CREATE ROLE pearl_super_admin WITH LOGIN;
                -- Password must be set separately via: ALTER ROLE pearl_super_admin WITH PASSWORD 'xxx';
            END IF;
            
            -- Grant BYPASSRLS to the role
            ALTER ROLE pearl_super_admin WITH BYPASSRLS;
            
            -- Grant necessary table permissions
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pearl_super_admin;
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pearl_super_admin;
        END
        $$;
    """)
    
    # ==========================================
    # Step 5: Enable RLS on tenant-aware tables
    # ==========================================
    
    for table in RLS_TABLES:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        
        # Force RLS even for table owner (critical for security)
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        
        # Create policy for tenant isolation
        # Uses current_setting with 'true' as second param to return NULL instead of error if not set
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
                FOR ALL
                USING (
                    tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
                )
                WITH CHECK (
                    tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::int
                )
        """)
    
    # ==========================================
    # Step 6: Grant permissions to app role
    # ==========================================
    
    # Create app role if it doesn't exist (for regular application connections)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pearl_app') THEN
                CREATE ROLE pearl_app WITH LOGIN;
            END IF;
            
            -- Grant table permissions (RLS will still apply)
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pearl_app;
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pearl_app;
        END
        $$;
    """)


def downgrade() -> None:
    # ==========================================
    # Remove RLS policies
    # ==========================================
    
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    
    # ==========================================
    # Restore global username uniqueness
    # ==========================================
    
    op.drop_constraint('uq_users_tenant_username', 'users', type_='unique')
    op.create_unique_constraint('users_username_key', 'users', ['username'])
    
    # ==========================================
    # Remove tenant_id from notifications
    # ==========================================
    
    op.drop_index('ix_notifications_tenant_user', 'notifications')
    op.drop_constraint('fk_notifications_tenant', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'tenant_id')
    
    # ==========================================
    # Remove tenant_id from app_settings
    # ==========================================
    
    op.drop_index('ix_app_settings_tenant', 'app_settings')
    op.drop_constraint('fk_app_settings_tenant', 'app_settings', type_='foreignkey')
    op.drop_column('app_settings', 'tenant_id')
    
    # Note: We don't drop the roles as they may be in use
    # They can be manually removed if needed
