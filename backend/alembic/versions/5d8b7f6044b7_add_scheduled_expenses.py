"""add scheduled expenses

Revision ID: 5d8b7f6044b7
Revises: 8b0251763a97
Create Date: 2026-03-04 23:33:43.095390

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '5d8b7f6044b7'
down_revision: Union[str, Sequence[str], None] = '8b0251763a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE IF NOT EXISTS scheduledfrequency AS ENUM ('WEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM')")
    op.execute("CREATE TYPE IF NOT EXISTS scheduledcategory AS ENUM ('SUBSCRIPTION', 'RECURRING', 'INSTALLMENT')")

    op.execute("""
        CREATE TABLE IF NOT EXISTS expenses_tracker.scheduled_expenses (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
            name             VARCHAR(100) NOT NULL,
            amount           FLOAT NOT NULL,
            account          expensecategory NOT NULL,
            frequency        scheduledfrequency NOT NULL,
            category         scheduledcategory NOT NULL,
            next_payment_date DATE,
            is_active        BOOLEAN NOT NULL DEFAULT true,
            icon             VARCHAR(10),
            color            VARCHAR(20),
            notes            TEXT,
            custom_days      INTEGER,
            created_at       TIMESTAMPTZ DEFAULT now(),
            updated_at       TIMESTAMPTZ
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS expenses_tracker.scheduled_expenses")
    op.execute("DROP TYPE IF EXISTS scheduledfrequency")
    op.execute("DROP TYPE IF EXISTS scheduledcategory")