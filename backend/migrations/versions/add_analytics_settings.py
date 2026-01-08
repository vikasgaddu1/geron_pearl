"""Add analytics default settings - finalize resource planning schema

Revision ID: add_analytics_settings
Revises: add_study_sister_relations
Create Date: 2026-01-07

Note: Analytics default settings (velocity lookback weeks, experience multipliers, etc.)
are handled in code with sensible defaults in the AnalyticsService class.
This migration finalizes the resource planning schema and serves as a placeholder
for any future analytics-specific database configuration.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_analytics_settings'
down_revision = 'add_study_sister_relations'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Analytics settings are managed in application code.
    Default values:
    - velocity_lookback_weeks: 8
    - capacity_forecast_weeks: 8
    - experience_multiplier_junior: 1.5
    - experience_multiplier_mid: 1.0
    - experience_multiplier_senior: 0.75
    - sister_study_reuse_factor: 0.5
    - over_allocation_threshold: 100
    """
    pass


def downgrade() -> None:
    pass
