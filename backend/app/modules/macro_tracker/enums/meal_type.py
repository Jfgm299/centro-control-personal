from enum import Enum as PyEnum


class MealType(str, PyEnum):
    BREAKFAST       = "breakfast"
    MORNING_SNACK   = "morning_snack"
    LUNCH           = "lunch"
    AFTERNOON_SNACK = "afternoon_snack"
    DINNER          = "dinner"
    OTHER           = "other"