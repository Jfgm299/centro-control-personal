import importlib
from typing import Any
from ..registry import registry
from .stop_handler import StopExecution


def handle(payload: dict, config: dict, db, user_id: int) -> dict:
    """
    Handler para triggers de sistema (manual, schedule_once, schedule_interval, webhook_inbound).
    El scheduler ya validó el timing antes de llamar al flow — solo pasa.
    """
    return {"matched": True}


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    trigger_id  = node_config.get("trigger_id")
    trigger_def = registry.get_trigger(trigger_id) if trigger_id else None

    if not trigger_def:
        # Trigger no registrado o sin trigger_id — pasar (backwards compat)
        return {"matched": True, "payload": ctx.get("payload", {})}

    handler = _import_handler(trigger_def.handler_path)
    result  = handler(
        payload=ctx.get("payload", {}),
        config=node_config,
        db=db,
        user_id=user_id,
    )

    if not result.get("matched"):
        raise StopExecution(result.get("reason", "trigger did not match"))

    return result


def _import_handler(handler_path: str):
    module_path, func_name = handler_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, func_name)