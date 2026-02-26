from enum import Enum as PyEnum

class MuscleGroupCategory(str, PyEnum):
    CHEST = 'Chest',
    BACK = 'Back',
    BICEPS = 'Biceps'
    TRICEPS = 'Triceps',
    CORE = 'Core',
    ABS = 'Abs',
    SHOULDERS = 'Shoulders',
    LEGS = 'Legs'