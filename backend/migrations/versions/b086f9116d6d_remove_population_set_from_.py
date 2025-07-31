"""Remove population_set from TextElementType enum

Revision ID: b086f9116d6d
Revises: 4bf0f677dea9
Create Date: 2025-07-31 16:03:58.254980

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b086f9116d6d'
down_revision = '4bf0f677dea9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create new enum without population_set
    new_textelementtype = postgresql.ENUM('title', 'footnote', name='textelementtype_new')
    new_textelementtype.create(op.get_bind())
    
    # Alter column to use new enum
    op.execute("ALTER TABLE text_elements ALTER COLUMN type TYPE textelementtype_new USING type::text::textelementtype_new")
    
    # Drop old enum and rename new one
    op.execute("DROP TYPE textelementtype")
    op.execute("ALTER TYPE textelementtype_new RENAME TO textelementtype")


def downgrade() -> None:
    # Create enum with population_set for rollback
    old_textelementtype = postgresql.ENUM('title', 'footnote', 'population_set', name='textelementtype_new')
    old_textelementtype.create(op.get_bind())
    
    # Alter column to use old enum
    op.execute("ALTER TABLE text_elements ALTER COLUMN type TYPE textelementtype_new USING type::text::textelementtype_new")
    
    # Drop new enum and rename old one
    op.execute("DROP TYPE textelementtype")
    op.execute("ALTER TYPE textelementtype_new RENAME TO textelementtype")