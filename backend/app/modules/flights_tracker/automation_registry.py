"""
Triggers y acciones que flights_tracker expone al motor de automatizaciones.

TRIGGERS:
    flights_tracker.flight_added             — Cuando se registra un vuelo
    flights_tracker.flight_status_changed    — Cuando el estado de un vuelo cambia
    flights_tracker.flight_departing_soon    — N horas antes de la salida

ACCIONES:
    flights_tracker.get_flight_details       — Obtener detalles completos de un vuelo
    flights_tracker.refresh_flight           — Actualizar datos del vuelo via AeroDataBox
"""


def register(registry) -> None:

    # ── TRIGGERS ──────────────────────────────────────────────────────────────

    registry.register_trigger(
        module_id="flights_tracker",
        trigger_id="flight_added",
        label="Cuando se registra un vuelo",
        config_schema={},
        handler="app.modules.flights_tracker.automation_handlers.handle_flight_added",
    )

    registry.register_trigger(
        module_id="flights_tracker",
        trigger_id="flight_status_changed",
        label="Cuando cambia el estado de un vuelo",
        config_schema={
            "to_status": {
                "type":     "enum[expected,check_in,boarding,gate_closed,departed,en_route,approaching,arrived,canceled,diverted,canceled_uncertain]",
                "label":    "Solo cuando el nuevo estado sea",
                "optional": True,
            },
        },
        handler="app.modules.flights_tracker.automation_handlers.handle_flight_status_changed",
    )

    registry.register_trigger(
        module_id="flights_tracker",
        trigger_id="flight_departing_soon",
        label="Cuando un vuelo sale pronto",
        config_schema={
            "hours_before": {
                "type":    "int",
                "label":   "Horas antes de la salida",
                "default": 24,
            },
        },
        handler="app.modules.flights_tracker.automation_handlers.handle_flight_departing_soon",
    )

    # ── ACCIONES ──────────────────────────────────────────────────────────────

    registry.register_action(
        module_id="flights_tracker",
        action_id="get_flight_details",
        label="Obtener detalles de un vuelo",
        config_schema={
            "flight_id": {
                "type":     "int",
                "label":    "ID del vuelo (si no viene del trigger)",
                "optional": True,
            },
            "fields": {
                "type":     "list[str]",
                "label":    "Campos a incluir (vacío = todos)",
                "optional": True,
                "default":  [],
            },
        },
        handler="app.modules.flights_tracker.automation_handlers.action_get_flight_details",
    )

    registry.register_action(
        module_id="flights_tracker",
        action_id="refresh_flight",
        label="Actualizar datos del vuelo via API",
        config_schema={
            "flight_id": {
                "type":     "int",
                "label":    "ID del vuelo (si no viene del trigger)",
                "optional": True,
            },
        },
        handler="app.modules.flights_tracker.automation_handlers.action_refresh_flight",
    )
