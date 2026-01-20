"""Add multi-tenancy foundation tables and columns.

This migration:
1. Creates subscription_plans table
2. Creates tenants table
3. Creates tenant_settings table
4. Creates super_admins table
5. Adds tenant_id to root entities (users, studies, packages, text_elements, audit_log, error_log)
6. Creates default tenant and migrates existing data
7. Creates composite indexes for multi-tenant queries

Revision ID: add_multi_tenancy_foundation
Revises: g8h9i0j1k2l3
Create Date: 2026-01-20
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta


# revision identifiers, used by Alembic.
revision = 'add_multi_tenancy_foundation'
down_revision = 'g8h9i0j1k2l3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================
    # Step 1: Create subscription_plans table
    # ==========================================
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('stripe_price_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_price_id_yearly', sa.String(length=255), nullable=True),
        sa.Column('price_monthly', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('price_yearly', sa.Integer(), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_studies', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_storage_mb', sa.Integer(), nullable=False, server_default='1024'),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Seed default plans
    op.execute("""
        INSERT INTO subscription_plans (name, display_name, description, price_monthly, price_yearly, max_users, max_studies, max_storage_mb, features, sort_order, is_active)
        VALUES 
        ('starter', 'Starter', 'Perfect for small teams getting started', 9900, 99000, 5, 10, 1024, '{"email_support": true, "api_access": false, "priority_support": false, "sso": false}', 1, 1),
        ('professional', 'Professional', 'For growing teams with advanced needs', 24900, 249000, 25, -1, 10240, '{"email_support": true, "api_access": true, "priority_support": true, "sso": false, "custom_branding": true}', 2, 1),
        ('enterprise', 'Enterprise', 'For large organizations with custom requirements', 0, 0, -1, -1, -1, '{"email_support": true, "api_access": true, "priority_support": true, "sso": true, "custom_branding": true, "dedicated_support": true, "custom_integrations": true}', 3, 1)
    """)
    
    # ==========================================
    # Step 2: Create tenants table
    # ==========================================
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('subscription_status', sa.Enum('trialing', 'active', 'past_due', 'canceled', 'unpaid', name='subscriptionstatus'), nullable=False, server_default='active'),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('grace_period_ends_at', sa.DateTime(), nullable=True),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('subscription_plans.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('stripe_customer_id')
    )
    op.create_index('ix_tenants_name', 'tenants', ['name'])
    
    # Create default tenant for existing data
    op.execute("""
        INSERT INTO tenants (id, name, display_name, subscription_status, is_active)
        VALUES (1, 'default', 'Default Tenant', 'active', 1)
    """)
    
    # ==========================================
    # Step 3: Create tenant_settings table
    # ==========================================
    op.create_table(
        'tenant_settings',
        sa.Column('tenant_id', sa.Integer(), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('date_format', sa.String(length=20), nullable=False, server_default='YYYY-MM-DD'),
        sa.Column('time_format', sa.String(length=20), nullable=False, server_default='HH:mm'),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('notification_email', sa.String(length=255), nullable=True),
        sa.Column('onboarding_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sample_data_active', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('tenant_id')
    )
    
    # Create settings for default tenant
    op.execute("""
        INSERT INTO tenant_settings (tenant_id, timezone, date_format, time_format, onboarding_completed, sample_data_active)
        VALUES (1, 'UTC', 'YYYY-MM-DD', 'HH:mm', 1, 0)
    """)
    
    # ==========================================
    # Step 4: Create super_admins table
    # ==========================================
    op.create_table(
        'super_admins',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('mfa_secret', sa.String(length=255), nullable=True),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('mfa_backup_codes', sa.String(length=1000), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(length=45), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_super_admins_email', 'super_admins', ['email'])
    
    # ==========================================
    # Step 5: Add tenant_id to existing tables
    # ==========================================
    
    # Users table
    op.add_column('users', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE users SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('users', 'tenant_id', nullable=False)
    op.create_foreign_key('fk_users_tenant', 'users', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_tenant_email', 'users', ['tenant_id', 'email'])
    op.create_index('ix_users_tenant_active', 'users', ['tenant_id', 'is_active'])
    
    # Studies table
    op.add_column('studies', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE studies SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('studies', 'tenant_id', nullable=False)
    op.create_foreign_key('fk_studies_tenant', 'studies', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_studies_tenant_id', 'studies', ['tenant_id'])
    op.create_index('ix_studies_tenant_created', 'studies', ['tenant_id', 'created_at'])
    # Drop global unique constraint on study_label and add tenant-scoped unique constraint
    op.drop_constraint('studies_study_label_key', 'studies', type_='unique')
    op.create_unique_constraint('uq_studies_tenant_label', 'studies', ['tenant_id', 'study_label'])
    
    # Packages table
    op.add_column('packages', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE packages SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('packages', 'tenant_id', nullable=False)
    op.create_foreign_key('fk_packages_tenant', 'packages', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_packages_tenant_id', 'packages', ['tenant_id'])
    op.create_index('ix_packages_tenant_created', 'packages', ['tenant_id', 'created_at'])
    op.create_unique_constraint('uq_packages_tenant_name', 'packages', ['tenant_id', 'package_name'])
    
    # Text elements table
    op.add_column('text_elements', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE text_elements SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('text_elements', 'tenant_id', nullable=False)
    op.create_foreign_key('fk_text_elements_tenant', 'text_elements', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_text_elements_tenant_id', 'text_elements', ['tenant_id'])
    op.create_index('ix_text_elements_tenant_type', 'text_elements', ['tenant_id', 'type'])
    
    # Audit log table
    op.add_column('audit_log', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.execute("UPDATE audit_log SET tenant_id = 1 WHERE tenant_id IS NULL")
    op.alter_column('audit_log', 'tenant_id', nullable=False)
    op.create_foreign_key('fk_audit_log_tenant', 'audit_log', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_audit_log_tenant_id', 'audit_log', ['tenant_id'])
    op.create_index('ix_audit_log_tenant_created', 'audit_log', ['tenant_id', 'created_at'])
    op.create_index('ix_audit_log_tenant_table', 'audit_log', ['tenant_id', 'table_name'])
    
    # Error log table (nullable tenant_id for unauthenticated errors)
    op.add_column('error_log', sa.Column('tenant_id', sa.Integer(), nullable=True))
    # Don't force update - error_log can have null tenant_id for unauthenticated errors
    op.create_foreign_key('fk_error_log_tenant', 'error_log', 'tenants', ['tenant_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_error_log_tenant_id', 'error_log', ['tenant_id'])
    op.create_index('ix_error_log_tenant_created', 'error_log', ['tenant_id', 'created_at'])
    op.create_index('ix_error_log_tenant_severity', 'error_log', ['tenant_id', 'severity'])


def downgrade() -> None:
    # Remove tenant_id from existing tables (reverse order)
    
    # Error log
    op.drop_index('ix_error_log_tenant_severity', 'error_log')
    op.drop_index('ix_error_log_tenant_created', 'error_log')
    op.drop_index('ix_error_log_tenant_id', 'error_log')
    op.drop_constraint('fk_error_log_tenant', 'error_log', type_='foreignkey')
    op.drop_column('error_log', 'tenant_id')
    
    # Audit log
    op.drop_index('ix_audit_log_tenant_table', 'audit_log')
    op.drop_index('ix_audit_log_tenant_created', 'audit_log')
    op.drop_index('ix_audit_log_tenant_id', 'audit_log')
    op.drop_constraint('fk_audit_log_tenant', 'audit_log', type_='foreignkey')
    op.drop_column('audit_log', 'tenant_id')
    
    # Text elements
    op.drop_index('ix_text_elements_tenant_type', 'text_elements')
    op.drop_index('ix_text_elements_tenant_id', 'text_elements')
    op.drop_constraint('fk_text_elements_tenant', 'text_elements', type_='foreignkey')
    op.drop_column('text_elements', 'tenant_id')
    
    # Packages
    op.drop_constraint('uq_packages_tenant_name', 'packages', type_='unique')
    op.drop_index('ix_packages_tenant_created', 'packages')
    op.drop_index('ix_packages_tenant_id', 'packages')
    op.drop_constraint('fk_packages_tenant', 'packages', type_='foreignkey')
    op.drop_column('packages', 'tenant_id')
    
    # Studies
    op.drop_constraint('uq_studies_tenant_label', 'studies', type_='unique')
    op.create_unique_constraint('studies_study_label_key', 'studies', ['study_label'])
    op.drop_index('ix_studies_tenant_created', 'studies')
    op.drop_index('ix_studies_tenant_id', 'studies')
    op.drop_constraint('fk_studies_tenant', 'studies', type_='foreignkey')
    op.drop_column('studies', 'tenant_id')
    
    # Users
    op.drop_index('ix_users_tenant_active', 'users')
    op.drop_index('ix_users_tenant_email', 'users')
    op.drop_index('ix_users_tenant_id', 'users')
    op.drop_constraint('fk_users_tenant', 'users', type_='foreignkey')
    op.drop_column('users', 'tenant_id')
    
    # Drop new tables
    op.drop_index('ix_super_admins_email', 'super_admins')
    op.drop_table('super_admins')
    
    op.drop_table('tenant_settings')
    
    op.drop_index('ix_tenants_name', 'tenants')
    op.drop_table('tenants')
    
    op.drop_table('subscription_plans')
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
