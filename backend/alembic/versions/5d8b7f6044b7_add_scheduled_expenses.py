"""add scheduled expenses

Revision ID: 5d8b7f6044b7
Revises: 8b0251763a97
Create Date: 2026-03-04 23:33:43.095390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d8b7f6044b7'
down_revision: Union[str, Sequence[str], None] = '8b0251763a97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scheduled_expenses',
        sa.Column('id',                 sa.Integer(),               nullable=False),
        sa.Column('user_id',            sa.Integer(),               nullable=False),
        sa.Column('name',               sa.String(length=100),      nullable=False),
        sa.Column('amount',             sa.Float(),                 nullable=False),
        sa.Column('account',            sa.Enum('REVOLUT', 'IMAGIN', name='expensecategory'), nullable=False),
        sa.Column('frequency',          sa.Enum('WEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM', name='scheduledfrequency'), nullable=False),
        sa.Column('category',           sa.Enum('SUBSCRIPTION', 'RECURRING', 'INSTALLMENT', name='scheduledcategory'), nullable=False),
        sa.Column('next_payment_date',  sa.Date(),                  nullable=True),
        sa.Column('is_active',          sa.Boolean(),               nullable=False, server_default='true'),
        sa.Column('icon',               sa.String(length=10),       nullable=True),
        sa.Column('color',              sa.String(length=20),       nullable=True),
        sa.Column('notes',              sa.Text(),                  nullable=True),
        sa.Column('custom_days',        sa.Integer(),               nullable=True),
        sa.Column('created_at',         sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at',         sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='expenses_tracker',
    )


def downgrade() -> None:
    op.drop_table('scheduled_expenses', schema='expenses_tracker')