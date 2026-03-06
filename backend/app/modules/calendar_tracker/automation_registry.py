"""
Triggers y acciones que calendar_tracker expone al motor de automatizaciones.

TRIGGERS:
    calendar_tracker.event_start           — Al iniciar un evento
    calendar_tracker.event_end             — Al finalizar un evento
    calendar_tracker.reminder_due          — Cuando vence un recordatorio
    calendar_tracker.no_events_in_window   — Cuando hay tiempo libre en una ventana futura
    calendar_tracker.overdue_reminders_exist — Cuando existen recordatorios vencidos sin programar

ACCIONES:
    calendar_tracker.create_event          — Crear un evento en el calendario
    calendar_tracker.create_reminder       — Crear un recordatorio
    calendar_tracker.mark_reminder_done    — Marcar un recordatorio como completado
    calendar_tracker.cancel_event          — Cancelar un evento
    calendar_tracker.push_summary_overdue  — Construir resumen de recordatorios vencidos
    calendar_tracker.get_todays_schedule   — Obtener todos los eventos de hoy
    calendar_tracker.bulk_mark_overdue_done — Marcar todos los vencidos como completados
"""




def register(registry) -> None:

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

    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="no_events_in_window",
        label="Cuando hay tiempo libre",
        config_schema={
            "window_hours":     {"type": "int", "label": "Horas a mirar hacia adelante", "default": 2},
            "min_free_minutes": {"type": "int", "label": "Minutos libres mínimos",       "default": 60},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_no_events_in_window",
    )

    registry.register_trigger(
        module_id="calendar_tracker",
        trigger_id="overdue_reminders_exist",
        label="Cuando existen recordatorios vencidos",
        config_schema={
            "min_count":    {"type": "int",                         "label": "Mínimo de recordatorios", "default": 1},
            "min_priority": {"type": "enum[low,medium,high,urgent]","label": "Prioridad mínima",        "default": "medium"},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.handle_overdue_reminders_exist",
    )

    # ── ACCIONES ──────────────────────────────────────────────────────────────

    registry.register_action(
        module_id="calendar_tracker",
        action_id="create_event",
        label="Crear evento en el calendario",
        config_schema={
            "title":                {"type": "str",  "label": "Título (soporta {{ vars.X }})"},
            "duration_minutes":     {"type": "int",  "label": "Duración en minutos",         "default": 30},
            "start_offset_minutes": {"type": "int",  "label": "Inicio en N minutos desde ahora", "default": 0},
            "category_id":          {"type": "int",  "label": "Categoría",                   "optional": True},
            "enable_dnd":           {"type": "bool", "label": "Activar DND",                 "default": False},
            "reminder_minutes":     {"type": "int",  "label": "Recordatorio previo (min)",   "optional": True},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_create_event",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="create_reminder",
        label="Crear recordatorio",
        config_schema={
            "title":       {"type": "str",                          "label": "Título"},
            "description": {"type": "str",                          "label": "Descripción",    "optional": True},
            "priority":    {"type": "enum[low,medium,high,urgent]", "label": "Prioridad",      "default": "medium"},
            "category_id": {"type": "int",                          "label": "Categoría",      "optional": True},
            "due_in_days": {"type": "int",                          "label": "Vence en N días","optional": True},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_create_reminder",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="mark_reminder_done",
        label="Marcar recordatorio como completado",
        config_schema={
            "reminder_id": {"type": "int", "label": "ID del recordatorio (o del payload)", "optional": True},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_mark_reminder_done",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="cancel_event",
        label="Cancelar un evento",
        config_schema={
            "event_id": {"type": "int", "label": "ID del evento (o del payload)", "optional": True},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_cancel_event",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="push_summary_overdue",
        label="Construir resumen de recordatorios vencidos",
        config_schema={
            "max_items":    {"type": "int",                          "label": "Máximo de items",  "default": 5},
            "min_priority": {"type": "enum[low,medium,high,urgent]", "label": "Prioridad mínima", "default": "medium"},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_push_summary_overdue",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="get_todays_schedule",
        label="Obtener eventos de hoy",
        config_schema={
            "category_ids":      {"type": "list[int]", "label": "Filtrar por categorías", "optional": True},
            "include_cancelled": {"type": "bool",      "label": "Incluir cancelados",     "default": False},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_get_todays_schedule",
    )

    registry.register_action(
        module_id="calendar_tracker",
        action_id="bulk_mark_overdue_done",
        label="Marcar todos los vencidos como completados",
        config_schema={
            "max_items":    {"type": "int",                          "label": "Máximo a marcar",  "default": 20},
            "min_priority": {"type": "enum[low,medium,high,urgent]", "label": "Prioridad mínima", "default": "low"},
        },
        handler="app.modules.calendar_tracker.services.automation_handlers.action_bulk_mark_overdue_done",
    )