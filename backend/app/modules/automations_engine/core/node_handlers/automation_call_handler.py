from typing import Any
from ...exceptions import FlowDepthExceededError, AutomationNotFoundError

MAX_DEPTH = 5


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    automation_id = node_config.get("automation_id")
    current_depth = ctx.get("_depth", 0)

    if current_depth + 1 > MAX_DEPTH:
        raise FlowDepthExceededError(MAX_DEPTH)

    # Import aquí para evitar circular imports
    from ...models.automation import Automation
    from ...services.flow_executor import flow_executor

    automation = db.query(Automation).filter(
        Automation.id      == automation_id,
        Automation.user_id == user_id,
        Automation.is_active == True,
    ).first()

    if not automation:
        raise AutomationNotFoundError(automation_id)

    child_ctx = {
        "payload": ctx.get("payload", {}),
        "vars":    {},
        "_depth":  current_depth + 1,
        "user_id": user_id,
    }

    result = flow_executor.execute_flow(
        flow=automation.flow,
        ctx=child_ctx,
        db=db,
        user_id=user_id,
    )

    return {"called_automation_id": automation_id, "result": result}