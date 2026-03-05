"""add one_time to scheduledcategory

Revision ID: b2c3d4e5f6a7
Revises: 5d8b7f6044b7
Create Date: 2026-03-05 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '5d8b7f6044b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE scheduledcategory ADD VALUE IF NOT EXISTS 'ONE_TIME'")


def downgrade() -> None:
    # PostgreSQL no permite eliminar valores de un enum
    # Para hacer downgrade habría que recrear el tipo
    pass