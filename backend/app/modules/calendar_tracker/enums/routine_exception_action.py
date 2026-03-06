from enum import Enum


class RoutineExceptionAction(str, Enum):
    CANCELLED = "cancelled"
    MODIFIED  = "modified"