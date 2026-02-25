from enum import Enum as PyEnum

class GymSetType(str, PyEnum):
    CARDIO = 'Cardio',
    WEIGHT_REPS = 'Weight_reps'