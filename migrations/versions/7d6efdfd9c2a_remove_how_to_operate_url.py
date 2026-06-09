"""Remove how_to_operate_url from solutions

Revision ID: 7d6efdfd9c2a
Revises: 44deb5318b78
Create Date: 2026-06-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d6efdfd9c2a"
down_revision = "44deb5318b78"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("solution", schema=None) as batch_op:
        batch_op.drop_column("how_to_operate_url")


def downgrade():
    with op.batch_alter_table("solution", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("how_to_operate_url", sa.String(), nullable=True)
        )
