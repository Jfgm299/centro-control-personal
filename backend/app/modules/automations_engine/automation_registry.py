# app/modules/automations_engine/automation_registry.py
"""
Registra los triggers y acciones del sistema (manual, schedule, webhook).
Este archivo es descubierto automáticamente por register_automation_handlers()
en module_loader.py al arrancar la app.
"""


def register(registry) -> None:

    # ── TRIGGERS ──────────────────────────────────────────────────────────────

    registry.register_trigger(
        module_id     = "system",
        trigger_id    = "manual",
        label         = "Manual",
        config_schema = {},
        handler       = "app.modules.automations_engine.core.node_handlers.trigger_handler.handle",
    )

    registry.register_trigger(
        module_id     = "system",
        trigger_id    = "schedule_once",
        label         = "A una hora exacta",
        config_schema = {
            "run_at": {"type": "datetime", "label": "Fecha y hora", "required": True},
        },
        handler       = "app.modules.automations_engine.core.node_handlers.trigger_handler.handle",
    )

    registry.register_trigger(
        module_id     = "system",
        trigger_id    = "schedule_interval",
        label         = "Cada X tiempo",
        config_schema = {
            "interval_value": {"type": "int",  "label": "Cada",   "required": True, "default": 30},
            "interval_unit":  {"type": "enum", "label": "Unidad", "required": True,
                               "options": ["minutes", "hours", "days"], "default": "minutes"},
            "active_from":    {"type": "time", "label": "Activo desde",  "required": False},
            "active_until":   {"type": "time", "label": "Activo hasta",  "required": False},
        },
        handler       = "app.modules.automations_engine.core.node_handlers.trigger_handler.handle",
    )

    registry.register_trigger(
        module_id     = "system",
        trigger_id    = "webhook_inbound",
        label         = "Webhook entrante",
        config_schema = {},
        handler       = "app.modules.automations_engine.core.node_handlers.trigger_handler.handle",
    )

    # ── ACCIONES DEL MOTOR ────────────────────────────────────────────────────
    # (outbound_webhook, delay y stop ya son nodos nativos del motor,
    #  pero los registramos también para que aparezcan en el registry del frontend)

    registry.register_action(
        module_id     = "automations_engine",
        action_id     = "outbound_webhook",
        label         = "HTTP request saliente",
        config_schema = {
            "url":     {"type": "string", "label": "URL",     "required": True},
            "method":  {"type": "enum",   "label": "Método",  "required": True,
                        "options": ["POST", "GET", "PUT", "PATCH", "DELETE"], "default": "POST"},
            "headers": {"type": "object", "label": "Cabeceras", "required": False},
            "body":    {"type": "text",   "label": "Body template", "required": False},
        },
        handler       = "app.modules.automations_engine.core.node_handlers.outbound_webhook_handler.handle",
    )

    registry.register_action(
        module_id     = "automations_engine",
        action_id     = "delay",
        label         = "Esperar N minutos",
        config_schema = {
            "delay_value": {"type": "int",  "label": "Tiempo",  "required": True, "default": 5},
            "delay_unit":  {"type": "enum", "label": "Unidad",  "required": True,
                            "options": ["minutes", "hours", "days"], "default": "minutes"},
        },
        handler       = "app.modules.automations_engine.core.node_handlers.delay_handler.handle",
    )

    registry.register_action(
        module_id     = "automations_engine",
        action_id     = "stop",
        label         = "Terminar flujo",
        config_schema = {
            "reason": {"type": "string", "label": "Motivo (opcional)", "required": False},
        },
        handler       = "app.modules.automations_engine.core.node_handlers.stop_handler.handle",
    )