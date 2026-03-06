"""
Handlers reales usados exclusivamente en tests.
Escriben en ctx['vars'] para que los tests puedan verificar que se ejecutaron.
"""


def handle_test_action(payload: dict, config: dict, db, user_id: int) -> dict:
    return {
        "executed": True,
        "received_payload": payload,
        "config_used": config,
    }


def handle_test_action_with_output(payload: dict, config: dict, db, user_id: int) -> dict:
    multiplier = config.get("multiplier", 1)
    value      = payload.get("value", 0)
    return {
        "executed": True,
        "result":   value * multiplier,
    }


def handle_test_action_that_fails(payload: dict, config: dict, db, user_id: int) -> dict:
    raise RuntimeError("Este handler falla a propósito")