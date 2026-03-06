from enum import Enum


class ReminderStatus(str, Enum):
    PENDING    = "pending"
    SCHEDULED  = "scheduled"
    DONE       = "done"