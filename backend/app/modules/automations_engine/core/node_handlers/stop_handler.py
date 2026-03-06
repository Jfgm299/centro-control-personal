from typing import Any


class StopExecution(Exception):
    """Excepción interna para detener el flujo limpiamente."""
    def __init__(self, reason: str = ""):
        self.reason = reason


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    reason = node_config.get("reason", "")
    raise StopExecution(reason=reason)