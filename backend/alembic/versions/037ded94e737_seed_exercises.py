"""seed_exercises - no-op (already applied locally)

Revision ID: 037ded94e737
Revises: fe20405602f3
Create Date: 2026-03-06 10:18:55.038051

"""
from typing import Sequence, Union

revision: str = '037ded94e737'
down_revision: Union[str, Sequence[str], None] = 'fe20405602f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass