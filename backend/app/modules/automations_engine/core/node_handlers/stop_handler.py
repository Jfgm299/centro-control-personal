from typing import Any


class StopExecution(Exception):
    """Excepción interna para detener el flujo limpiamente."""
    def __init__(self, reason: str = ""):
        self.reason = reason


def handle(payload: dict, config: dict, db, user_id: int) -> dict:
    """Adapter para ser llamado desde action_handler vía registry."""
    ctx = {"payload": payload, "vars": {}, "_depth": 0, "user_id": user_id}
    return execute(config, ctx, db, user_id)


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    reason = node_config.get("reason", "")
    raise StopExecution(reason=reason)