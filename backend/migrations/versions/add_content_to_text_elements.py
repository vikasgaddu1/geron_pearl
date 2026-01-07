"""Add content column to text_elements

Revision ID: add_content_to_text_elements
Revises: df7267a2f25d
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_content_to_text_elements'
down_revision = 'df7267a2f25d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'text_elements',
        sa.Column('content', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('text_elements', 'content')



