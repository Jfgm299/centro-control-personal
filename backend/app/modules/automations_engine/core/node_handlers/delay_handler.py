from typing import Any
import time


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    """
    En la implementación síncrona hace un sleep real.
    En la implementación async (APScheduler) se reemplaza por una tarea programada.
    """
    minutes = node_config.get("minutes", 1)
    seconds = min(minutes * 60, 300)  # máximo 5 minutos en modo síncrono
    time.sleep(seconds)
    return {"delayed_seconds": seconds}