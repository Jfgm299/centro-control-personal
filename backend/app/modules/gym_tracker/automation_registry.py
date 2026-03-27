"""
Triggers y acciones que gym_tracker expone al motor de automatizaciones.

TRIGGERS:
    gym_tracker.workout_started             — Cuando se inicia un workout
    gym_tracker.workout_ended               — Cuando se termina un workout
    gym_tracker.personal_record_weight      — Cuando se establece un récord personal de peso
    gym_tracker.body_measurement_recorded   — Cuando se registra una medición corporal
    gym_tracker.workout_inactivity          — Cuando el usuario lleva N días sin entrenar

ACCIONES:
    gym_tracker.get_last_workout_summary    — Resumen del último workout terminado
    gym_tracker.get_weekly_stats            — Estadísticas de la semana
    gym_tracker.get_exercise_progression    — Progresión de un ejercicio
    gym_tracker.get_body_measurement_trend  — Tendencia de mediciones corporales
"""


def register(registry) -> None:

    # ── TRIGGERS ──────────────────────────────────────────────────────────────

    registry.register_trigger(
        module_id="gym_tracker",
        trigger_id="workout_started",
        label="Cuando se inicia un workout",
        config_schema={
            "day_of_week": {
                "type":     "enum[monday,tuesday,wednesday,thursday,friday,saturday,sunday]",
                "label":    "Solo en este día de la semana",
                "optional": True,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.handle_workout_started",
    )

    registry.register_trigger(
        module_id="gym_tracker",
        trigger_id="workout_ended",
        label="Cuando se termina un workout",
        config_schema={
            "min_duration_minutes": {
                "type":     "int",
                "label":    "Duración mínima (minutos)",
                "optional": True,
            },
            "max_duration_minutes": {
                "type":     "int",
                "label":    "Duración máxima (minutos)",
                "optional": True,
            },
            "min_exercises": {
                "type":     "int",
                "label":    "Número mínimo de ejercicios",
                "optional": True,
            },
            "min_sets": {
                "type":     "int",
                "label":    "Número mínimo de series",
                "optional": True,
            },
            "required_muscle_groups": {
                "type":     "list[str]",
                "label":    "Grupos musculares obligatorios (valores del enum)",
                "optional": True,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.handle_workout_ended",
    )

    registry.register_trigger(
        module_id="gym_tracker",
        trigger_id="personal_record_weight",
        label="Cuando se establece un récord personal de peso",
        config_schema={
            "exercise_name": {
                "type":     "str",
                "label":    "Solo para este ejercicio (vacío = cualquiera)",
                "optional": True,
            },
            "min_weight_kg": {
                "type":     "int",
                "label":    "Solo si el nuevo récord supera este peso (kg)",
                "optional": True,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.handle_personal_record_weight",
    )

    registry.register_trigger(
        module_id="gym_tracker",
        trigger_id="body_measurement_recorded",
        label="Cuando se registra una medición corporal",
        config_schema={
            "min_weight_kg": {
                "type":     "int",
                "label":    "Solo si el peso es mayor o igual a (kg)",
                "optional": True,
            },
            "max_weight_kg": {
                "type":     "int",
                "label":    "Solo si el peso es menor o igual a (kg)",
                "optional": True,
            },
            "require_body_fat": {
                "type":     "bool",
                "label":    "Requerir que incluya % grasa corporal",
                "optional": True,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.handle_body_measurement_recorded",
    )

    registry.register_trigger(
        module_id="gym_tracker",
        trigger_id="workout_inactivity",
        label="Cuando el usuario lleva N días sin entrenar",
        config_schema={
            "days_without_workout": {
                "type":  "int",
                "label": "Días sin entrenar para disparar",
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.handle_workout_inactivity",
    )

    # ── ACCIONES ──────────────────────────────────────────────────────────────

    registry.register_action(
        module_id="gym_tracker",
        action_id="get_last_workout_summary",
        label="Obtener resumen del último workout",
        config_schema={
            "workout_id": {
                "type":     "int",
                "label":    "ID del workout (vacío = último terminado)",
                "optional": True,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.action_get_last_workout_summary",
    )

    registry.register_action(
        module_id="gym_tracker",
        action_id="get_weekly_stats",
        label="Obtener estadísticas de la semana",
        config_schema={
            "week_offset": {
                "type":    "int",
                "label":   "Semana (0 = actual, -1 = anterior)",
                "default": 0,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.action_get_weekly_stats",
    )

    registry.register_action(
        module_id="gym_tracker",
        action_id="get_exercise_progression",
        label="Obtener progresión de un ejercicio",
        config_schema={
            "exercise_name": {
                "type":  "str",
                "label": "Nombre del ejercicio",
            },
            "limit": {
                "type":    "int",
                "label":   "Número de sesiones a devolver",
                "default": 10,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.action_get_exercise_progression",
    )

    registry.register_action(
        module_id="gym_tracker",
        action_id="get_body_measurement_trend",
        label="Obtener tendencia de mediciones corporales",
        config_schema={
            "limit": {
                "type":    "int",
                "label":   "Número de mediciones más recientes",
                "default": 5,
            },
        },
        handler="app.modules.gym_tracker.automation_handlers.action_get_body_measurement_trend",
    )
