from enum import Enum


class AutomationTriggerType(str, Enum):
    MODULE_EVENT = "module_event"
    WEBHOOK      = "webhook"
    CRON         = "cron"


class NodeType(str, Enum):
    TRIGGER          = "trigger"
    CONDITION        = "condition"
    ACTION           = "action"
    OUTBOUND_WEBHOOK = "outbound_webhook"
    AUTOMATION_CALL  = "automation_call"
    DELAY            = "delay"
    STOP             = "stop"


class ConditionOperator(str, Enum):
    EQ         = "eq"
    NEQ        = "neq"
    GT         = "gt"
    LT         = "lt"
    CONTAINS   = "contains"
    EXISTS     = "exists"
    NOT_EXISTS = "not_exists"