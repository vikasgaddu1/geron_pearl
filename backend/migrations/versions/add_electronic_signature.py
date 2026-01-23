"""Add electronic signature feature

Adds TOTP-based electronic signature capability to reporting efforts.
Signatures are permanent and cannot be reversed (unlike locks).

Revision ID: add_electronic_signature
Revises: ebe30a019c99
Create Date: 2026-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_electronic_signature'
down_revision = 'remove_sample_data_seeded'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # 1. Add signature TOTP fields to users table
    # ==========================================================================
    op.add_column('users', sa.Column(
        'signature_secret_encrypted', sa.String(), nullable=True,
        comment='Fernet-encrypted TOTP secret for e-signatures'
    ))
    op.add_column('users', sa.Column(
        'signature_backup_codes_encrypted', sa.String(), nullable=True,
        comment='Fernet-encrypted backup codes (comma-separated)'
    ))
    op.add_column('users', sa.Column(
        'signature_setup_completed', sa.Boolean(), nullable=False, server_default='false',
        comment='Whether TOTP setup is verified'
    ))
    op.add_column('users', sa.Column(
        'signature_failed_attempts', sa.Integer(), nullable=False, server_default='0',
        comment='Failed TOTP attempts for rate limiting'
    ))
    op.add_column('users', sa.Column(
        'signature_locked_until', sa.DateTime(), nullable=True,
        comment='Lockout expiry after failed attempts'
    ))

    # ==========================================================================
    # 2. Add signature fields to reporting_efforts table
    # ==========================================================================
    op.add_column('reporting_efforts', sa.Column(
        'is_signed', sa.Boolean(), nullable=False, server_default='false'
    ))
    op.add_column('reporting_efforts', sa.Column(
        'signed_at', sa.DateTime(timezone=True), nullable=True,
        comment='UTC timestamp when signed'
    ))
    op.add_column('reporting_efforts', sa.Column(
        'signed_by_id', sa.Integer(), nullable=True
    ))
    op.add_column('reporting_efforts', sa.Column(
        'signature_hash', sa.String(512), nullable=True,
        comment='SHA256:hexdigest for verification'
    ))
    op.add_column('reporting_efforts', sa.Column(
        'signature_reason', sa.Text(), nullable=True,
        comment='Required reason/intent for signing'
    ))

    # Add foreign key for signed_by_id with SET NULL on delete
    op.create_foreign_key(
        'fk_reporting_efforts_signed_by_id_users',
        'reporting_efforts', 'users',
        ['signed_by_id'], ['id'],
        ondelete='SET NULL'
    )

    # ==========================================================================
    # 3. Create reporting_effort_signature_history table
    # ==========================================================================
    op.create_table(
        'reporting_effort_signature_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reporting_effort_id', sa.Integer(), nullable=False),
        sa.Column('signed_by_id', sa.Integer(), nullable=True),
        sa.Column('signed_by_username', sa.String(255), nullable=False,
                  comment='Username at time of signing (preserved for audit)'),
        sa.Column('signature_hash', sa.String(512), nullable=False,
                  comment='SHA256:hexdigest of signature data'),
        sa.Column('reason', sa.Text(), nullable=False,
                  comment='Required reason/intent for signing'),
        sa.Column('items_snapshot', sa.Text(), nullable=False,
                  comment='JSON snapshot of all items at time of signing'),
        sa.Column('items_count', sa.Integer(), nullable=False,
                  comment='Number of items at time of signing'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  comment='When the signature was created (UTC)'),
        sa.Column('ip_address', sa.String(45), nullable=True,
                  comment='IP address of signer (IPv4 or IPv6)'),
        sa.Column('user_agent', sa.String(500), nullable=True,
                  comment='Browser/client user agent string'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['reporting_effort_id'], ['reporting_efforts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['signed_by_id'], ['users.id'], ondelete='SET NULL')
    )

    # Create indexes for efficient queries
    op.create_index(
        'ix_reporting_effort_signature_history_reporting_effort_id',
        'reporting_effort_signature_history',
        ['reporting_effort_id']
    )
    op.create_index(
        'ix_reporting_effort_signature_history_signed_by_id',
        'reporting_effort_signature_history',
        ['signed_by_id']
    )
    op.create_index(
        'ix_reporting_effort_signature_history_created_at',
        'reporting_effort_signature_history',
        ['created_at']
    )


def downgrade() -> None:
    # ==========================================================================
    # 1. Drop reporting_effort_signature_history table
    # ==========================================================================
    op.drop_index('ix_reporting_effort_signature_history_created_at',
                  table_name='reporting_effort_signature_history')
    op.drop_index('ix_reporting_effort_signature_history_signed_by_id',
                  table_name='reporting_effort_signature_history')
    op.drop_index('ix_reporting_effort_signature_history_reporting_effort_id',
                  table_name='reporting_effort_signature_history')
    op.drop_table('reporting_effort_signature_history')

    # ==========================================================================
    # 2. Remove signature fields from reporting_efforts table
    # ==========================================================================
    op.drop_constraint('fk_reporting_efforts_signed_by_id_users', 'reporting_efforts', type_='foreignkey')
    op.drop_column('reporting_efforts', 'signature_reason')
    op.drop_column('reporting_efforts', 'signature_hash')
    op.drop_column('reporting_efforts', 'signed_by_id')
    op.drop_column('reporting_efforts', 'signed_at')
    op.drop_column('reporting_efforts', 'is_signed')

    # ==========================================================================
    # 3. Remove signature TOTP fields from users table
    # ==========================================================================
    op.drop_column('users', 'signature_locked_until')
    op.drop_column('users', 'signature_failed_attempts')
    op.drop_column('users', 'signature_setup_completed')
    op.drop_column('users', 'signature_backup_codes_encrypted')
    op.drop_column('users', 'signature_secret_encrypted')
