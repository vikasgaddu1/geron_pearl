"""drop_acronym_related_tables_and_fix_text_elements_enum

Revision ID: 7a7096093ce9
Revises: b086f9116d6d
Create Date: 2025-07-31 18:23:35.633262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a7096093ce9'
down_revision = 'b086f9116d6d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop acronym-related tables in correct order (foreign key dependencies)
    op.execute("DROP TABLE IF EXISTS acronym_set_members CASCADE")
    op.execute("DROP TABLE IF EXISTS acronym_sets CASCADE")
    op.execute("DROP TABLE IF EXISTS acronyms CASCADE")
    
    # Drop and recreate text_elements table to fix enum issues
    # First backup any data (since user said dummy data is OK to lose, we'll just recreate)
    op.execute("DROP TABLE IF EXISTS text_elements CASCADE")
    
    # Drop old enum type
    op.execute("DROP TYPE IF EXISTS textelementtype CASCADE")
    op.execute("DROP TYPE IF EXISTS textelementtype_new CASCADE")
    
    # Create new enum type without population_set
    op.execute("CREATE TYPE textelementtype AS ENUM ('title', 'footnote')")
    
    # Recreate text_elements table
    op.execute("""
        CREATE TABLE text_elements (
            id SERIAL PRIMARY KEY,
            type textelementtype NOT NULL DEFAULT 'title',
            label TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_text_elements_type ON text_elements (type)")


def downgrade() -> None:
    # This migration is destructive and cannot be fully reversed
    # Tables and data would need to be recreated manually
    print("WARNING: This migration drops tables and cannot be reversed without data loss")
    pass