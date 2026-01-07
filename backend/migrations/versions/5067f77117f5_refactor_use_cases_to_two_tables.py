"""refactor_use_cases_to_two_tables

Revision ID: 5067f77117f5
Revises: 404a7ba0700b
Create Date: 2026-01-06 18:42:36.340632

Refactors use_cases from a fixed ARRAY column on reporting_efforts to a
flexible two-table system with use case definitions and many-to-many assignments.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5067f77117f5'
down_revision = '404a7ba0700b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect
    from alembic import op as alembic_op

    bind = alembic_op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # Create use case definitions table (if not exists)
    if 'reporting_effort_usecases' not in existing_tables:
        op.create_table(
            'reporting_effort_usecases',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('color', sa.String(length=7), nullable=False, server_default='#3B82F6'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_reporting_effort_usecases_id'), 'reporting_effort_usecases', ['id'], unique=False)
        op.create_index(op.f('ix_reporting_effort_usecases_name'), 'reporting_effort_usecases', ['name'], unique=True)

    # Create use case assignments (many-to-many) table (if not exists)
    if 'reporting_effort_usecase_assignments' not in existing_tables:
        op.create_table(
            'reporting_effort_usecase_assignments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('reporting_effort_id', sa.Integer(), nullable=False),
            sa.Column('use_case_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['reporting_effort_id'], ['reporting_efforts.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['use_case_id'], ['reporting_effort_usecases.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('reporting_effort_id', 'use_case_id', name='uq_effort_usecase')
        )
        op.create_index(op.f('ix_reporting_effort_usecase_assignments_id'), 'reporting_effort_usecase_assignments', ['id'], unique=False)
        op.create_index(op.f('ix_reporting_effort_usecase_assignments_reporting_effort_id'), 'reporting_effort_usecase_assignments', ['reporting_effort_id'], unique=False)
        op.create_index(op.f('ix_reporting_effort_usecase_assignments_use_case_id'), 'reporting_effort_usecase_assignments', ['use_case_id'], unique=False)

    # Drop the old ARRAY column from reporting_efforts (if exists)
    columns = [col['name'] for col in inspector.get_columns('reporting_efforts')]
    if 'use_cases' in columns:
        op.drop_column('reporting_efforts', 'use_cases')


def downgrade() -> None:
    # Re-add the old ARRAY column
    from sqlalchemy.dialects import postgresql
    op.add_column('reporting_efforts', sa.Column('use_cases', postgresql.ARRAY(sa.String(length=50)), nullable=True))

    # Drop the new tables
    op.drop_index(op.f('ix_reporting_effort_usecase_assignments_use_case_id'), table_name='reporting_effort_usecase_assignments')
    op.drop_index(op.f('ix_reporting_effort_usecase_assignments_reporting_effort_id'), table_name='reporting_effort_usecase_assignments')
    op.drop_index(op.f('ix_reporting_effort_usecase_assignments_id'), table_name='reporting_effort_usecase_assignments')
    op.drop_table('reporting_effort_usecase_assignments')

    op.drop_index(op.f('ix_reporting_effort_usecases_name'), table_name='reporting_effort_usecases')
    op.drop_index(op.f('ix_reporting_effort_usecases_id'), table_name='reporting_effort_usecases')
    op.drop_table('reporting_effort_usecases')
