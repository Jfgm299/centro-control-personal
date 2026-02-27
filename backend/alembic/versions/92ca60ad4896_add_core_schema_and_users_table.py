"""add core schema and users table

Revision ID: 92ca60ad4896
Revises: 5393539151ea
Create Date: 2026-02-26 23:30:39.822353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '92ca60ad4896'
down_revision: Union[str, Sequence[str], None] = '5393539151ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Crear tabla users (nueva)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        schema='core'
    )
    op.create_index(op.f('ix_core_users_email'), 'users', ['email'], unique=True, schema='core')

    # Añadir user_id a tablas existentes
    op.add_column('workouts',
        sa.Column('user_id', sa.Integer(), nullable=False),
        schema='gym_tracker'
    )
    op.create_foreign_key(
        'fk_workouts_user_id', 'workouts', 'users',
        ['user_id'], ['id'],
        source_schema='gym_tracker', referent_schema='core',
        ondelete='CASCADE'
    )

    op.add_column('body_measurements',
        sa.Column('user_id', sa.Integer(), nullable=False),
        schema='gym_tracker'
    )
    op.create_foreign_key(
        'fk_body_measurements_user_id', 'body_measurements', 'users',
        ['user_id'], ['id'],
        source_schema='gym_tracker', referent_schema='core',
        ondelete='CASCADE'
    )

    op.add_column('expenses',
        sa.Column('user_id', sa.Integer(), nullable=False),
        schema='expenses_tracker'
    )
    op.create_foreign_key(
        'fk_expenses_user_id', 'expenses', 'users',
        ['user_id'], ['id'],
        source_schema='expenses_tracker', referent_schema='core',
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_expenses_user_id', 'expenses', schema='expenses_tracker', type_='foreignkey')
    op.drop_column('expenses', 'user_id', schema='expenses_tracker')

    op.drop_constraint('fk_body_measurements_user_id', 'body_measurements', schema='gym_tracker', type_='foreignkey')
    op.drop_column('body_measurements', 'user_id', schema='gym_tracker')

    op.drop_constraint('fk_workouts_user_id', 'workouts', schema='gym_tracker', type_='foreignkey')
    op.drop_column('workouts', 'user_id', schema='gym_tracker')

    op.drop_index(op.f('ix_core_users_email'), table_name='users', schema='core')
    op.drop_table('users', schema='core')