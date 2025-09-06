"""re-adds date column to materials table to fix deployment issue"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'hotfix01'
down_revision = '288fb98f9629'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('materials', sa.Column('date', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('materials', 'date')
