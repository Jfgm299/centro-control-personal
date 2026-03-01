import enum


class ActivityCategory(str, enum.Enum):
    sightseeing     = "sightseeing"
    food            = "food"
    transport       = "transport"
    accommodation   = "accommodation"
    activity        = "activity"
    other           = "other"