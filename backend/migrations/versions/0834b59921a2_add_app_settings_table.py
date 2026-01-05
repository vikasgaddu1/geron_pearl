"""Add app_settings table

Revision ID: 0834b59921a2
Revises: df7267a2f25d
Create Date: 2026-01-05 12:19:51.831818

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0834b59921a2'
down_revision = 'df7267a2f25d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), nullable=False, default=1),
        sa.Column('default_due_date_offset', sa.Integer(), nullable=False, default=7,
                  comment='Default number of days to add when auto-setting due dates'),
        sa.Column('updated_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['updated_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.CheckConstraint('id = 1', name='single_row')
    )

    # Insert default settings row
    op.execute("""
        INSERT INTO app_settings (id, default_due_date_offset)
        VALUES (1, 7)
    """)


def downgrade() -> None:
    op.drop_table('app_settings')