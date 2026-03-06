from typing import Any


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    """
    El trigger solo valida que el payload existe.
    La ejecución real la inicia el servicio que detecta el evento.
    """
    return {"matched": True, "payload": ctx.get("payload", {})}