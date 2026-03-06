"""seed_exercises

Revision ID: 037ded94e737
Revises: fe20405602f3
Create Date: 2026-03-06 10:18:55.038051

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '037ded94e737'
down_revision: Union[str, Sequence[str], None] = 'fe20405602f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ADD VALUE no puede usarse dentro de una transacción.
    # COMMIT cierra la transacción abierta por Alembic, luego BEGIN abre una nueva
    # para el INSERT, que ya puede ver los nuevos valores del enum.
    conn = op.get_bind()
    conn.execute(sa.text("COMMIT"))
    conn.execute(sa.text("ALTER TYPE gymsettype ADD VALUE IF NOT EXISTS 'Cardio'"))
    conn.execute(sa.text("ALTER TYPE gymsettype ADD VALUE IF NOT EXISTS 'Weight_reps'"))
    conn.execute(sa.text("ALTER TYPE gymsettype ADD VALUE IF NOT EXISTS 'Bodyweight'"))
    conn.execute(sa.text("BEGIN"))

    op.execute("""
        INSERT INTO gym_tracker.exercise_catalog
            (name, exercise_type, muscle_groups, is_custom, user_id)
        VALUES
        ('Bench Press',         'Weight_reps', '["Chest","Triceps"]',     false, null),
        ('Incline Bench Press', 'Weight_reps', '["Chest","Shoulders"]',   false, null),
        ('Chest Fly',           'Weight_reps', '["Chest"]',               false, null),
        ('Cable Crossover',     'Weight_reps', '["Chest"]',               false, null),
        ('Push-ups',            'Bodyweight',  '["Chest","Triceps"]',     false, null),
        ('Dips',                'Bodyweight',  '["Chest","Triceps"]',     false, null),
        ('Pull-ups',            'Bodyweight',  '["Back","Biceps"]',       false, null),
        ('Chin-ups',            'Bodyweight',  '["Back","Biceps"]',       false, null),
        ('Barbell Row',         'Weight_reps', '["Back","Biceps"]',       false, null),
        ('Lat Pulldown',        'Weight_reps', '["Back"]',                false, null),
        ('Seated Cable Row',    'Weight_reps', '["Back","Biceps"]',       false, null),
        ('Deadlift',            'Weight_reps', '["Back","Legs"]',         false, null),
        ('T-Bar Row',           'Weight_reps', '["Back"]',                false, null),
        ('Barbell Curl',        'Weight_reps', '["Biceps"]',              false, null),
        ('Dumbbell Curl',       'Weight_reps', '["Biceps"]',              false, null),
        ('Hammer Curl',         'Weight_reps', '["Biceps"]',              false, null),
        ('Preacher Curl',       'Weight_reps', '["Biceps"]',              false, null),
        ('Tricep Pushdown',     'Weight_reps', '["Triceps"]',             false, null),
        ('Skull Crushers',      'Weight_reps', '["Triceps"]',             false, null),
        ('Overhead Tricep Ext', 'Weight_reps', '["Triceps"]',             false, null),
        ('Close Grip Bench',    'Weight_reps', '["Triceps","Chest"]',     false, null),
        ('Overhead Press',      'Weight_reps', '["Shoulders","Triceps"]', false, null),
        ('Lateral Raise',       'Weight_reps', '["Shoulders"]',           false, null),
        ('Front Raise',         'Weight_reps', '["Shoulders"]',           false, null),
        ('Arnold Press',        'Weight_reps', '["Shoulders"]',           false, null),
        ('Face Pull',           'Weight_reps', '["Shoulders","Back"]',    false, null),
        ('Squat',               'Weight_reps', '["Legs"]',                false, null),
        ('Leg Press',           'Weight_reps', '["Legs"]',                false, null),
        ('Romanian Deadlift',   'Weight_reps', '["Legs","Back"]',         false, null),
        ('Leg Curl',            'Weight_reps', '["Legs"]',                false, null),
        ('Leg Extension',       'Weight_reps', '["Legs"]',                false, null),
        ('Calf Raise',          'Weight_reps', '["Legs"]',                false, null),
        ('Lunges',              'Weight_reps', '["Legs"]',                false, null),
        ('Plank',               'Bodyweight',  '["Core","Abs"]',          false, null),
        ('Side Plank',          'Bodyweight',  '["Core"]',                false, null),
        ('Crunch',              'Bodyweight',  '["Abs"]',                 false, null),
        ('Bicycle Crunch',      'Bodyweight',  '["Abs"]',                 false, null),
        ('Leg Raise',           'Bodyweight',  '["Abs","Core"]',          false, null),
        ('Ab Wheel',            'Bodyweight',  '["Abs","Core"]',          false, null),
        ('Russian Twist',       'Bodyweight',  '["Abs","Core"]',          false, null),
        ('Cable Crunch',        'Weight_reps', '["Abs"]',                 false, null),
        ('Running',             'Cardio',      '[]',                      false, null),
        ('Cycling',             'Cardio',      '[]',                      false, null),
        ('Elliptical',          'Cardio',      '[]',                      false, null),
        ('Rowing Machine',      'Cardio',      '[]',                      false, null),
        ('Jump Rope',           'Cardio',      '[]',                      false, null)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM gym_tracker.exercise_catalog WHERE user_id IS NULL")