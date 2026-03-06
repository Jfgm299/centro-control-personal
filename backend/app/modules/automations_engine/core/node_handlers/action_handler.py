import importlib
from typing import Any
from ...core.registry import registry
from ...exceptions import ActionNotFoundInRegistryError


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    action_id  = node_config.get("action_id")
    action_def = registry.get_action(action_id)

    if not action_def:
        raise ActionNotFoundInRegistryError(action_id)

    handler = _import_handler(action_def.handler_path)
    result  = handler(
        payload=ctx.get("payload", {}),
        config=node_config,
        db=db,
        user_id=user_id,
    )
    return result


def _import_handler(handler_path: str):
    module_path, func_name = handler_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, func_name)