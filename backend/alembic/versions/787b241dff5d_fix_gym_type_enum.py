"""normalize_gymsettype_values - no-op (already applied locally)

Revision ID: normalize_gymsettype
Revises: 037ded94e737
Create Date: 2026-03-06

"""
from typing import Sequence, Union

revision: str = 'normalize_gymsettype'
down_revision: Union[str, Sequence[str], None] = '037ded94e737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass