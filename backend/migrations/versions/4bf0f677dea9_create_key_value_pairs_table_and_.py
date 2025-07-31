"""Create key_value_pairs table and migrate from acronyms and text_elements

Revision ID: 4bf0f677dea9
Revises: 473053e83a5b
Create Date: 2025-07-31 16:03:19.544337

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4bf0f677dea9'
down_revision = '473053e83a5b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create KeyValueType enum if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE keyvaluetype AS ENUM ('acronym', 'population_set');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create key_value_pairs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS key_value_pairs (
            id SERIAL PRIMARY KEY,
            type keyvaluetype NOT NULL,
            key VARCHAR(100) NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_key_value_type_key UNIQUE (type, key)
        )
    """)
    
    # Create indexes if they don't exist
    op.execute("CREATE INDEX IF NOT EXISTS ix_key_value_pairs_type ON key_value_pairs (type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_key_value_pairs_key ON key_value_pairs (key)")
    
    # Migrate data from acronyms table
    op.execute("""
        INSERT INTO key_value_pairs (type, key, value, description, created_at, updated_at)
        SELECT 'acronym', key, value, description, created_at, updated_at
        FROM acronyms
    """)
    
    # Migrate population_set data from text_elements table
    op.execute("""
        INSERT INTO key_value_pairs (type, key, value, description, created_at, updated_at)
        SELECT 'population_set', 
               CONCAT('Pop_', id::text) as key,
               label as value,
               NULL as description,
               created_at,
               updated_at
        FROM text_elements 
        WHERE type = 'population_set'
    """)
    
    # Remove population_set records from text_elements
    op.execute("DELETE FROM text_elements WHERE type = 'population_set'")


def downgrade() -> None:
    # Restore acronyms data
    op.execute("""
        INSERT INTO acronyms (key, value, description, created_at, updated_at)
        SELECT key, value, description, created_at, updated_at
        FROM key_value_pairs
        WHERE type = 'acronym'
    """)
    
    # Restore population_set records to text_elements
    op.execute("""
        INSERT INTO text_elements (type, label, created_at, updated_at)
        SELECT 'population_set', value, created_at, updated_at
        FROM key_value_pairs
        WHERE type = 'population_set'
    """)
    
    # Drop key_value_pairs table
    op.drop_index(op.f('ix_key_value_pairs_key'), table_name='key_value_pairs')
    op.drop_index(op.f('ix_key_value_pairs_type'), table_name='key_value_pairs')
    op.drop_table('key_value_pairs')
    
    # Drop the enum
    keyvaluetype = postgresql.ENUM('acronym', 'population_set', name='keyvaluetype')
    keyvaluetype.drop(op.get_bind())