"""add ich_category to text element type

Revision ID: add_ich_category
Revises: 037667cf7ced_merge_comment_type_and_study_label
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ich_category'
down_revision = '037667cf7ced'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ich_category to the textelementtype enum
    # PostgreSQL requires ALTER TYPE to add enum values
    op.execute("ALTER TYPE textelementtype ADD VALUE IF NOT EXISTS 'ich_category'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type, which is complex
    pass

