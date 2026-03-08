import httpx
import re
from typing import Any


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


def _resolve_template(template: Any, ctx: dict) -> Any:
    flat = {**ctx.get("payload", {}), **ctx.get("vars", {})}
    if isinstance(template, str):
        return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", lambda m: str(flat.get(m.group(1), "")), template)
    if isinstance(template, dict):
        return {k: _resolve_template(v, ctx) for k, v in template.items()}
    if isinstance(template, list):
        return [_resolve_template(i, ctx) for i in template]
    return template