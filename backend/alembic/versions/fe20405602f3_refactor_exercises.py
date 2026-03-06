"""refactor_exercises

Revision ID: fe20405602f3
Revises: b2c3d4e5f6a7
Create Date: 2026-03-05 23:24:48.605699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = 'fe20405602f3'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Asegurar que el enum tiene todos los valores necesarios ANTES de usarlo
    op.execute("ALTER TYPE gymsettype ADD VALUE IF NOT EXISTS 'Cardio'")
    op.execute("ALTER TYPE gymsettype ADD VALUE IF NOT EXISTS 'Weight_reps'")
    op.execute("ALTER TYPE gymsettype ADD VALUE IF NOT EXISTS 'Bodyweight'")

    # 2. Crear tabla con exercise_type como Text primero (evita el error de cast)
    op.create_table(
        'exercise_catalog',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('exercise_type', sa.Text(), nullable=False),
        sa.Column('muscle_groups', JSON, nullable=False, server_default='[]'),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('core.users.id', ondelete='CASCADE'),
            nullable=True,
        ),
        schema='gym_tracker',
    )

    # 3. Añadir columnas a exercises
    op.add_column(
        'exercises',
        sa.Column('muscle_groups', JSON, nullable=False, server_default='[]'),
        schema='gym_tracker',
    )
    op.add_column(
        'exercises',
        sa.Column(
            'catalog_id',
            sa.Integer(),
            sa.ForeignKey('gym_tracker.exercise_catalog.id', ondelete='SET NULL'),
            nullable=True,
        ),
        schema='gym_tracker',
    )

    # 4. Seed con valores de texto (la columna es Text todavía, no falla)
    op.execute("""
        INSERT INTO gym_tracker.exercise_catalog
            (name, exercise_type, muscle_groups, is_custom, user_id)
        VALUES
        ('Bench Press',          'Weight_reps', '["Chest","Triceps"]',     false, null),
        ('Incline Bench Press',  'Weight_reps', '["Chest","Shoulders"]',   false, null),
        ('Chest Fly',            'Weight_reps', '["Chest"]',               false, null),
        ('Cable Crossover',      'Weight_reps', '["Chest"]',               false, null),
        ('Push-ups',             'Bodyweight',  '["Chest","Triceps"]',     false, null),
        ('Dips',                 'Bodyweight',  '["Chest","Triceps"]',     false, null),
        ('Pull-ups',             'Bodyweight',  '["Back","Biceps"]',       false, null),
        ('Chin-ups',             'Bodyweight',  '["Back","Biceps"]',       false, null),
        ('Barbell Row',          'Weight_reps', '["Back","Biceps"]',       false, null),
        ('Lat Pulldown',         'Weight_reps', '["Back"]',                false, null),
        ('Seated Cable Row',     'Weight_reps', '["Back","Biceps"]',       false, null),
        ('Deadlift',             'Weight_reps', '["Back","Legs"]',         false, null),
        ('T-Bar Row',            'Weight_reps', '["Back"]',                false, null),
        ('Barbell Curl',         'Weight_reps', '["Biceps"]',              false, null),
        ('Dumbbell Curl',        'Weight_reps', '["Biceps"]',              false, null),
        ('Hammer Curl',          'Weight_reps', '["Biceps"]',              false, null),
        ('Preacher Curl',        'Weight_reps', '["Biceps"]',              false, null),
        ('Tricep Pushdown',      'Weight_reps', '["Triceps"]',             false, null),
        ('Skull Crushers',       'Weight_reps', '["Triceps"]',             false, null),
        ('Overhead Tricep Ext',  'Weight_reps', '["Triceps"]',             false, null),
        ('Close Grip Bench',     'Weight_reps', '["Triceps","Chest"]',     false, null),
        ('Overhead Press',       'Weight_reps', '["Shoulders","Triceps"]', false, null),
        ('Lateral Raise',        'Weight_reps', '["Shoulders"]',           false, null),
        ('Front Raise',          'Weight_reps', '["Shoulders"]',           false, null),
        ('Arnold Press',         'Weight_reps', '["Shoulders"]',           false, null),
        ('Face Pull',            'Weight_reps', '["Shoulders","Back"]',    false, null),
        ('Squat',                'Weight_reps', '["Legs"]',                false, null),
        ('Leg Press',            'Weight_reps', '["Legs"]',                false, null),
        ('Romanian Deadlift',    'Weight_reps', '["Legs","Back"]',         false, null),
        ('Leg Curl',             'Weight_reps', '["Legs"]',                false, null),
        ('Leg Extension',        'Weight_reps', '["Legs"]',                false, null),
        ('Calf Raise',           'Weight_reps', '["Legs"]',                false, null),
        ('Lunges',               'Weight_reps', '["Legs"]',                false, null),
        ('Plank',                'Bodyweight',  '["Core","Abs"]',          false, null),
        ('Side Plank',           'Bodyweight',  '["Core"]',                false, null),
        ('Crunch',               'Bodyweight',  '["Abs"]',                 false, null),
        ('Bicycle Crunch',       'Bodyweight',  '["Abs"]',                 false, null),
        ('Leg Raise',            'Bodyweight',  '["Abs","Core"]',          false, null),
        ('Ab Wheel',             'Bodyweight',  '["Abs","Core"]',          false, null),
        ('Russian Twist',        'Bodyweight',  '["Abs","Core"]',          false, null),
        ('Cable Crunch',         'Weight_reps', '["Abs"]',                 false, null),
        ('Running',              'Cardio',      '[]',                      false, null),
        ('Cycling',              'Cardio',      '[]',                      false, null),
        ('Elliptical',           'Cardio',      '[]',                      false, null),
        ('Rowing Machine',       'Cardio',      '[]',                      false, null),
        ('Jump Rope',            'Cardio',      '[]',                      false, null)
    """)

    # 5. Ahora convertir la columna Text -> gymsettype (el enum ya tiene los valores)
    op.execute("""
        ALTER TABLE gym_tracker.exercise_catalog
        ALTER COLUMN exercise_type TYPE gymsettype
        USING exercise_type::gymsettype
    """)


def downgrade():
    op.drop_column('exercises', 'catalog_id', schema='gym_tracker')
    op.drop_column('exercises', 'muscle_groups', schema='gym_tracker')
    op.drop_table('exercise_catalog', schema='gym_tracker')