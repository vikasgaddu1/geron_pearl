"""revert_to_text_elements_with_four_types

Revision ID: c7087c378307
Revises: 7a7096093ce9
Create Date: 2025-07-31 18:43:29.919269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7087c378307'
down_revision = '7a7096093ce9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop key_value_pairs table and related enum
    op.execute("DROP TABLE IF EXISTS key_value_pairs CASCADE")
    op.execute("DROP TYPE IF EXISTS keyvaluetype CASCADE")
    
    # Drop and recreate text_elements table with expanded enum
    op.execute("DROP TABLE IF EXISTS text_elements CASCADE")
    op.execute("DROP TYPE IF EXISTS textelementtype CASCADE")
    
    # Create new enum type with all four values
    op.execute("CREATE TYPE textelementtype AS ENUM ('title', 'footnote', 'population_set', 'acronyms_set')")
    
    # Recreate text_elements table with expanded enum
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
    pass