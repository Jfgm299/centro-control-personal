from . import (
    trigger_handler,
    condition_handler,
    action_handler,
    outbound_webhook_handler,
    automation_call_handler,
    delay_handler,
    stop_handler,
)

NODE_HANDLERS = {
    "trigger":          trigger_handler,
    "condition":        condition_handler,
    "action":           action_handler,
    "outbound_webhook": outbound_webhook_handler,
    "automation_call":  automation_call_handler,
    "delay":            delay_handler,
    "stop":             stop_handler,
}