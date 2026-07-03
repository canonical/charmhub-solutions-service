"""Add categories to solution

Revision ID: b1f2c3d4e5a6
Revises: 7d6efdfd9c2a
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b1f2c3d4e5a6"
down_revision = "7d6efdfd9c2a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("solution", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("categories", sa.JSON(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("solution", schema=None) as batch_op:
        batch_op.drop_column("categories")
