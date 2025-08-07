"""add_packages_system_tables

Revision ID: d3f89a2c4b56
Revises: c7087c378307
Create Date: 2025-08-07 16:10:58.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3f89a2c4b56'
down_revision = 'c7087c378307'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create packages table
    op.create_table('packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_packages_package_name'), 'packages', ['package_name'], unique=False)
    
    # Create package_items table (enum will be created automatically by SQLAlchemy)
    op.create_table('package_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('study_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.Enum('TLF', 'Dataset', name='itemtype'), nullable=False),
        sa.Column('item_subtype', sa.String(length=50), nullable=False),
        sa.Column('item_code', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ),
        sa.ForeignKeyConstraint(['study_id'], ['studies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('package_id', 'item_type', 'item_subtype', 'item_code', name='uq_package_item_unique')
    )
    op.create_index(op.f('ix_package_items_item_type'), 'package_items', ['item_type'], unique=False)
    op.create_index(op.f('ix_package_items_package_id'), 'package_items', ['package_id'], unique=False)
    op.create_index(op.f('ix_package_items_study_id'), 'package_items', ['study_id'], unique=False)
    
    # Create package_tlf_details table
    op.create_table('package_tlf_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_item_id', sa.Integer(), nullable=False),
        sa.Column('title_id', sa.Integer(), nullable=True),
        sa.Column('population_flag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['package_item_id'], ['package_items.id'], ),
        sa.ForeignKeyConstraint(['title_id'], ['text_elements.id'], ),
        sa.ForeignKeyConstraint(['population_flag_id'], ['text_elements.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_package_tlf_details_package_item_id'), 'package_tlf_details', ['package_item_id'], unique=True)
    
    # Create package_dataset_details table
    op.create_table('package_dataset_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_item_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('sorting_order', sa.Integer(), nullable=True),
        sa.Column('acronyms', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['package_item_id'], ['package_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_package_dataset_details_package_item_id'), 'package_dataset_details', ['package_item_id'], unique=True)
    
    # Create package_item_footnotes junction table
    op.create_table('package_item_footnotes',
        sa.Column('package_item_id', sa.Integer(), nullable=False),
        sa.Column('footnote_id', sa.Integer(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['package_item_id'], ['package_items.id'], ),
        sa.ForeignKeyConstraint(['footnote_id'], ['text_elements.id'], ),
        sa.PrimaryKeyConstraint('package_item_id', 'footnote_id')
    )
    
    # Create package_item_acronyms junction table
    op.create_table('package_item_acronyms',
        sa.Column('package_item_id', sa.Integer(), nullable=False),
        sa.Column('acronym_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['package_item_id'], ['package_items.id'], ),
        sa.ForeignKeyConstraint(['acronym_id'], ['text_elements.id'], ),
        sa.PrimaryKeyConstraint('package_item_id', 'acronym_id')
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('package_item_acronyms')
    op.drop_table('package_item_footnotes')
    op.drop_index(op.f('ix_package_dataset_details_package_item_id'), table_name='package_dataset_details')
    op.drop_table('package_dataset_details')
    op.drop_index(op.f('ix_package_tlf_details_package_item_id'), table_name='package_tlf_details')
    op.drop_table('package_tlf_details')
    op.drop_index(op.f('ix_package_items_study_id'), table_name='package_items')
    op.drop_index(op.f('ix_package_items_package_id'), table_name='package_items')
    op.drop_index(op.f('ix_package_items_item_type'), table_name='package_items')
    op.drop_table('package_items')
    op.drop_index(op.f('ix_packages_package_name'), table_name='packages')
    op.drop_table('packages')
    
    # Drop enum type (SQLAlchemy should handle this but we ensure it's dropped)
    op.execute("DROP TYPE IF EXISTS itemtype")