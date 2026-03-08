# automations_engine

Schema: `automations` | Es el motor de automatizaciones — no expone automation contract propio.

Motor de automatizaciones basado en grafos. Permite a los usuarios crear flujos visuales (nodos + edges) que se ejecutan cuando un módulo dispara un trigger.

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `Automation` | `automations.automations` | Definición del flujo (nombre, trigger, `flow` JSON) |
| `Execution` | `automations.executions` | Historial de ejecuciones de un flujo |
| `ApiKey` | `automations.api_keys` | API keys para trigger por webhook externo |
| `WebhookInbound` | `automations.webhook_inbounds` | Configuración de webhook entrante |

## User Relationships

```python
user.automations       # List[Automation]
user.auto_executions   # List[Execution]
user.api_keys          # List[ApiKey]
user.inbound_webhooks  # List[WebhookInbound]
```

## Trigger Types (`AutomationTriggerType`)

| Valor | Descripción |
|-------|-------------|
| `module_event` | Disparado por un módulo (ej: `calendar_tracker.event_start`) |
| `webhook` | Disparado por llamada HTTP externa (inbound webhook) |
| `cron` | Disparado por schedule periódico |

## Graph Model

Un flujo (`Automation.flow`) es un JSON con `nodes` y `edges`:

```json
{
  "nodes": [
    {"id": "n1", "type": "trigger", "config": {"ref": "calendar_tracker.event_start", ...}},
    {"id": "n2", "type": "condition", "config": {"field": "event.category_id", "op": "eq", "value": 5}},
    {"id": "n3", "type": "action", "config": {"ref": "calendar_tracker.create_reminder", ...}}
  ],
  "edges": [
    {"from": "n1", "to": "n2"},
    {"from": "n2", "to": "n3", "when": "true"}
  ]
}
```

**Edge `when`:** `null` = siempre, `"true"` = si condition fue true, `"false"` = si condition fue false.

## Node Types

| Tipo | Handler | Qué hace |
|------|---------|----------|
| `trigger` | `trigger_handler.py` | Primer nodo — evalúa si el trigger se cumple |
| `condition` | `condition_handler.py` | Evalúa condición sobre el contexto; devuelve `condition_result: bool` |
| `action` | `action_handler.py` | Ejecuta una acción de módulo |
| `outbound_webhook` | `outbound_webhook_handler.py` | Hace HTTP POST a URL externa |
| `automation_call` | `automation_call_handler.py` | Llama a otro flujo de automatización |
| `delay` | `delay_handler.py` | Pausa la ejecución N segundos |
| `stop` | `stop_handler.py` | Detiene el flujo (lanza `StopExecution`) |

## Condition Operators (`ConditionOperator`)

`eq`, `neq`, `gt`, `lt`, `contains`, `exists`, `not_exists`

El campo se resuelve con dot notation sobre el contexto: `"event.category_id"`, `"vars.node_n1.matched"`, etc.

## Execution Context (`ctx`)

```python
ctx = {
    "payload": {...},        # datos del trigger original
    "vars": {
        "node_n1": {...},    # output de cada nodo, accesible por nodos siguientes
        "node_n2": {...},
    },
    "user_id": int,
    "_depth": int,           # profundidad de recursión (automation_call)
}
```

## Flow Executor (`flow_executor.py`)

```python
result = flow_executor.execute(automation, payload, db, user_id)
# result = {"status": "success"|"failed"|"skipped", "node_logs": [...]}
```

También soporta `execute_stream()` — versión generator que hace `yield` de eventos por nodo en tiempo real (para el frontend):
- `{"type": "node_start", "node_id": "n1"}`
- `{"type": "node", "node_id": "n1", "status": "success", "duration_ms": 42, "output": {...}}`
- `{"type": "done", "status": "success", "duration_ms": 123, "node_logs": [...]}`

## Services

| Service | Responsabilidad |
|---------|----------------|
| `automation_service.py` | CRUD automations |
| `execution_service.py` | Crear y actualizar registros de ejecución |
| `flow_executor.py` | Ejecutar flujos (sync y streaming) |
| `api_key_service.py` | Gestión de API keys |
| `webhook_service.py` | Gestión de inbound webhooks |

## Automation Registry (`core/registry.py`)

Singleton global `registry` que se llena al arrancar la app. Los módulos se registran en él llamando a `register_automation_handlers(registry)` desde `module_loader`. Ver `@docs/module-system.md` para el contrato completo.
