from typing import Any
import time

UNIT_TO_SECONDS = {
    'seconds': 1,
    'minutes': 60,
    'hours':   3600,
    'days':    86400,
}

MAX_SECONDS = 300  # máximo 5 minutos en modo síncrono


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    """
    Espera N segundos/minutos/horas/días antes de continuar el flujo.
    En modo síncrono el máximo es 5 minutos (300s).
    """
    value = node_config.get("delay_value") or node_config.get("minutes", 1)
    unit  = node_config.get("delay_unit", "minutes")

    multiplier     = UNIT_TO_SECONDS.get(unit, 60)
    total_seconds  = int(value) * multiplier
    capped_seconds = min(total_seconds, MAX_SECONDS)

    time.sleep(capped_seconds)

    return {
        "delayed_seconds": capped_seconds,
        "requested_value": value,
        "requested_unit":  unit,
        "capped":          total_seconds > MAX_SECONDS,
    }