"""
Registro de triggers y acciones de calendar_tracker en el motor de automatizaciones.
Este archivo es descubierto automáticamente por module_loader.register_automation_handlers().
No importa nada de automations_engine directamente — recibe el registry como parámetro.
"""


def register(registry) -> None:
    """
    Registra los triggers y acciones que calendar_tracker expone
    al motor de automatizaciones.
    """

    # ── TRIGGERS ──────────────────────────────────────────────────────────────

    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="event_start",
        label="Al iniciar un evento",
        config_schema={
            "category_ids":    {"type": "list[int]", "label": "Solo estas categorías", "optional": True},
            "advance_minutes": {"type": "int",       "label": "Minutos de antelación", "default": 0},
            "enable_dnd_only": {"type": "bool",      "label": "Solo si DND activo",    "default": False},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_event_start",
    )

    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="event_end",
        label="Al finalizar un evento",
        config_schema={
            "category_ids": {"type": "list[int]", "label": "Solo estas categorías", "optional": True},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_event_end",
    )

    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="reminder_due",
        label="Cuando vence un recordatorio",
        config_schema={
            "min_priority": {
                "type":    "enum[low,medium,high,urgent]",
                "label":   "Prioridad mínima",
                "default": "high",
            },
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_reminder_due",
    )

    # ── ACCIONES ──────────────────────────────────────────────────────────────

    registry.register_action(
        module_id="calendar_tracker",
        action_id="create_event",
        label="Crear evento en el calendario",
        config_schema={
            "title":            {"type": "str", "label": "Título"},
            "duration_minutes": {"type": "int", "label": "Duración en minutos", "default": 30},
            "category_id":      {"type": "int", "label": "Categoría",           "optional": True},
            "enable_dnd":       {"type": "bool","label": "Activar DND",         "default": False},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_create_event",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="push_summary_overdue",
        label="Notificar recordatorios vencidos",
        config_schema={},
        handler="app.modules.calendar_tracker.services.automation_handlers.action_push_summary_overdue",
    )