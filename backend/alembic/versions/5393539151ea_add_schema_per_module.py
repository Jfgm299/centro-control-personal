"""add schema per module

Revision ID: 5393539151ea
Revises: 5a55be2323e9
Create Date: 2026-02-26 21:09:09.032230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5393539151ea'
down_revision: Union[str, Sequence[str], None] = '5a55be2323e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Crear los nuevos esquemas si no existen
    op.execute('CREATE SCHEMA IF NOT EXISTS expenses_tracker;')
    op.execute('CREATE SCHEMA IF NOT EXISTS gym_tracker;')

    # 2. Mover los tipos ENUM (que son los que causaban el error) a los nuevos esquemas
    op.execute('ALTER TYPE public.expensecategory SET SCHEMA expenses_tracker;')
    op.execute('ALTER TYPE public.gymsettype SET SCHEMA gym_tracker;')
    op.execute('ALTER TYPE public.musclegroupcategory SET SCHEMA gym_tracker;')

    # 3. Mover las tablas al esquema expenses_tracker
    op.execute('ALTER TABLE public.expenses SET SCHEMA expenses_tracker;')

    # 4. Mover las tablas al esquema gym_tracker
    op.execute('ALTER TABLE public.body_measurements SET SCHEMA gym_tracker;')
    op.execute('ALTER TABLE public.workouts SET SCHEMA gym_tracker;')
    op.execute('ALTER TABLE public.exercises SET SCHEMA gym_tracker;')
    op.execute('ALTER TABLE public.workout_muscle_groups SET SCHEMA gym_tracker;')
    op.execute('ALTER TABLE public.sets SET SCHEMA gym_tracker;')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Devolver las tablas al esquema public original
    op.execute('ALTER TABLE expenses_tracker.expenses SET SCHEMA public;')
    
    op.execute('ALTER TABLE gym_tracker.body_measurements SET SCHEMA public;')
    op.execute('ALTER TABLE gym_tracker.workouts SET SCHEMA public;')
    op.execute('ALTER TABLE gym_tracker.exercises SET SCHEMA public;')
    op.execute('ALTER TABLE gym_tracker.workout_muscle_groups SET SCHEMA public;')
    op.execute('ALTER TABLE gym_tracker.sets SET SCHEMA public;')

    # 2. Devolver los tipos ENUM al esquema public original
    op.execute('ALTER TYPE expenses_tracker.expensecategory SET SCHEMA public;')
    op.execute('ALTER TYPE gym_tracker.gymsettype SET SCHEMA public;')
    op.execute('ALTER TYPE gym_tracker.musclegroupcategory SET SCHEMA public;')

    # 3. Eliminar los esquemas creados
    op.execute('DROP SCHEMA IF EXISTS expenses_tracker;')
    op.execute('DROP SCHEMA IF EXISTS gym_tracker;')