"""add refresh tokens table

Revision ID: 859a005d0d9c
Revises: 92ca60ad4896
Create Date: 2026-02-27 14:28:42.178738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '859a005d0d9c'
down_revision: Union[str, Sequence[str], None] = '92ca60ad4896'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('refresh_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='core'
    )
    op.create_index(op.f('ix_core_refresh_tokens_token'), 'refresh_tokens', ['token'], unique=True, schema='core')


def downgrade() -> None:
    op.drop_index(op.f('ix_core_refresh_tokens_token'), table_name='refresh_tokens', schema='core')
    op.drop_table('refresh_tokens', schema='core')