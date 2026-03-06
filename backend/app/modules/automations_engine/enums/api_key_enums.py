from enum import Enum


class ApiKeyScope(str, Enum):
    TRIGGER = "trigger"
    READ    = "read"