"""fix_gym_type_enum

Revision ID: 787b241dff5d
Revises: 037ded94e737
Create Date: 2026-03-06 10:28:03.744829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '787b241dff5d'
down_revision: Union[str, Sequence[str], None] = '037ded94e737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # COMMIT para poder usar ALTER TYPE fuera de transacción
    conn.execute(sa.text("COMMIT"))

    # Renombrar valores uppercase → mixedcase en gym_tracker.gymsettype
    conn.execute(sa.text("ALTER TYPE gym_tracker.gymsettype RENAME VALUE 'CARDIO' TO 'Cardio'"))
    conn.execute(sa.text("ALTER TYPE gym_tracker.gymsettype RENAME VALUE 'WEIGHT_REPS' TO 'Weight_reps'"))

    # Añadir Bodyweight si no existe (idempotente)
    conn.execute(sa.text("ALTER TYPE gym_tracker.gymsettype ADD VALUE IF NOT EXISTS 'Bodyweight'"))

    conn.execute(sa.text("BEGIN"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("COMMIT"))
    conn.execute(sa.text("ALTER TYPE gym_tracker.gymsettype RENAME VALUE 'Cardio' TO 'CARDIO'"))
    conn.execute(sa.text("ALTER TYPE gym_tracker.gymsettype RENAME VALUE 'Weight_reps' TO 'WEIGHT_REPS'"))
    conn.execute(sa.text("BEGIN"))