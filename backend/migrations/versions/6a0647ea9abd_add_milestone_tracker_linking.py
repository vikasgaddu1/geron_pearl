"""add_milestone_tracker_linking

Revision ID: 6a0647ea9abd
Revises: 5067f77117f5
Create Date: 2026-01-07 10:31:32.263019

Adds milestone-tracker linking support:
- linked_subtype column on milestones for subtype-based auto-linking
- linked_tag_id column on milestones for tag-based auto-linking
- milestone_tracker_assignments junction table for manual linking
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a0647ea9abd'
down_revision = '5067f77117f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the junction table for manual milestone-tracker assignments
    op.create_table('milestone_tracker_assignments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=False),
        sa.Column('tracker_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['milestone_id'], ['reporting_effort_milestones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tracker_id'], ['reporting_effort_item_tracker.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('milestone_id', 'tracker_id', name='uq_milestone_tracker')
    )
    op.create_index(op.f('ix_milestone_tracker_assignments_milestone_id'), 'milestone_tracker_assignments', ['milestone_id'], unique=False)
    op.create_index(op.f('ix_milestone_tracker_assignments_tracker_id'), 'milestone_tracker_assignments', ['tracker_id'], unique=False)

    # Add linking columns to milestones
    op.add_column('reporting_effort_milestones', sa.Column('linked_subtype', sa.String(length=50), nullable=True))
    op.add_column('reporting_effort_milestones', sa.Column('linked_tag_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_reporting_effort_milestones_linked_tag_id'), 'reporting_effort_milestones', ['linked_tag_id'], unique=False)
    op.create_foreign_key('fk_milestone_linked_tag', 'reporting_effort_milestones', 'tracker_tags', ['linked_tag_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Remove linking columns from milestones
    op.drop_constraint('fk_milestone_linked_tag', 'reporting_effort_milestones', type_='foreignkey')
    op.drop_index(op.f('ix_reporting_effort_milestones_linked_tag_id'), table_name='reporting_effort_milestones')
    op.drop_column('reporting_effort_milestones', 'linked_tag_id')
    op.drop_column('reporting_effort_milestones', 'linked_subtype')

    # Drop the junction table
    op.drop_index(op.f('ix_milestone_tracker_assignments_tracker_id'), table_name='milestone_tracker_assignments')
    op.drop_index(op.f('ix_milestone_tracker_assignments_milestone_id'), table_name='milestone_tracker_assignments')
    op.drop_table('milestone_tracker_assignments')
