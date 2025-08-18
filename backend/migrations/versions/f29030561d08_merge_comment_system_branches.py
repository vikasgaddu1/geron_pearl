"""merge comment system branches

Revision ID: f29030561d08
Revises: 686b7f37d8ad, ccff86bd596b
Create Date: 2025-08-18 08:54:10.093344

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f29030561d08'
down_revision = ('686b7f37d8ad', 'ccff86bd596b')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass