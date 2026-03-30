import httpx
import re
from typing import Any


def handle(payload: dict, config: dict, db, user_id: int) -> dict:
    """Adapter para ser llamado desde action_handler vía registry."""
    ctx = {"payload": payload, "vars": {}, "_depth": 0, "user_id": user_id}
    return execute(config, ctx, db, user_id)


def execute(node_config: dict, ctx: dict, db, user_id: int) -> dict[str, Any]:
    url     = node_config.get("url")
    method  = node_config.get("method", "POST").upper()
    headers = node_config.get("headers", {})
    timeout = node_config.get("timeout_seconds", 10)
    body_template = node_config.get("body_template", {})

    resolved_body = _resolve_template(body_template, ctx)

    try:
        response = httpx.request(
            method=method,
            url=url,
            json=resolved_body,
            headers=headers,
            timeout=timeout,
        )
        return {
            "status_code": response.status_code,
            "success":     response.is_success,
            "body":        response.text[:1000],
        }
    except httpx.TimeoutException:
        return {"success": False, "error": "timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _resolve_path(data: dict, path: str) -> Any:
    parts = path.split(".")
    val = data
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


def _resolve_template(template: Any, ctx: dict) -> Any:
    flat = {**ctx.get("payload", {}), **ctx.get("vars", {})}
    if isinstance(template, str):
        return re.sub(
            r"\{\{\s*([\w.]+)\s*\}\}",
            lambda m: str(_resolve_path(flat, m.group(1)) or ""),
            template,
        )
    if isinstance(template, dict):
        return {k: _resolve_template(v, ctx) for k, v in template.items()}
    if isinstance(template, list):
        return [_resolve_template(i, ctx) for i in template]
    return template