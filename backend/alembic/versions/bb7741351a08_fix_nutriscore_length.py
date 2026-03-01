"""fix_nutriscore_length

Revision ID: bb7741351a08
Revises: f93834db0e4a
Create Date: 2026-03-01 10:46:07.241003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bb7741351a08'
down_revision: Union[str, Sequence[str], None] = 'f93834db0e4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'products',
        'nutriscore',
        existing_type=sa.String(length=1),
        type_=sa.String(length=10),
        existing_nullable=True,
        schema='macro_tracker',
    )


def downgrade() -> None:
    op.alter_column(
        'products',
        'nutriscore',
        existing_type=sa.String(length=10),
        type_=sa.String(length=1),
        existing_nullable=True,
        schema='macro_tracker',
    )