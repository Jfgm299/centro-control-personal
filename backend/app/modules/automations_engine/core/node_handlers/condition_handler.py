from typing import Any
from ...enums import ConditionOperator


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    field_path = node_config.get("field", "")
    operator   = node_config.get("op", ConditionOperator.EQ)
    value      = node_config.get("value")

    data       = {**ctx.get("payload", {}), **ctx.get("vars", {})}
    field_val  = _resolve_field(data, field_path)

    result = _evaluate(field_val, operator, value)
    return {"condition_result": result, "matched": result}


def _resolve_field(data: dict, path: str) -> Any:
    parts = path.split(".")
    val = data
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


def _evaluate(field_val: Any, operator: str, value: Any) -> bool:
    try:
        match operator:
            case ConditionOperator.EQ:         return field_val == value
            case ConditionOperator.NEQ:        return field_val != value
            case ConditionOperator.GT:         return field_val is not None and field_val > value
            case ConditionOperator.LT:         return field_val is not None and field_val < value
            case ConditionOperator.CONTAINS:   return value in field_val if field_val is not None else False
            case ConditionOperator.EXISTS:     return field_val is not None
            case ConditionOperator.NOT_EXISTS: return field_val is None
            case _:                            return False
    except TypeError:
        return False