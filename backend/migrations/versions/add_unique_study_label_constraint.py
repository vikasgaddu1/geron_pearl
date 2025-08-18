"""Add unique constraint on study_label to prevent duplicates

Revision ID: add_unique_study_label_constraint
Revises: add_cascade_delete_constraints
Create Date: 2025-01-18 17:00:00.000000

This migration adds a UNIQUE constraint on the study_label column to prevent 
duplicate study names from being created in the future.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'unique_study_label'
down_revision = 'add_cascade_delete_constraints'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """
    Add UNIQUE constraint on study_label column.
    """
    
    print("🛡️ Adding UNIQUE constraint on study_label...")
    
    # Add unique constraint on study_label
    print("  - Adding UNIQUE constraint on studies.study_label")
    op.create_unique_constraint(
        'uq_studies_study_label',  # constraint name
        'studies',                 # table name
        ['study_label']           # column(s)
    )
    
    print("✅ UNIQUE constraint added successfully!")
    print("🎯 Duplicate study labels are now prevented at database level!")


def downgrade() -> None:
    """
    Remove UNIQUE constraint on study_label column.
    
    WARNING: This will allow duplicate study labels again!
    Only use this for debugging or if you need to rollback for a specific reason.
    """
    
    print("⚠️  Removing UNIQUE constraint on study_label...")
    print("   This will allow duplicate study labels again!")
    
    # Remove unique constraint
    op.drop_constraint('uq_studies_study_label', 'studies', type_='unique')
    
    print("⚠️  UNIQUE constraint removed!")
    print("🚨 WARNING: Duplicate study labels are now possible again!")
