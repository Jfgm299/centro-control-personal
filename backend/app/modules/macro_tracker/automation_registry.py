"""
Triggers y acciones que macro_tracker expone al motor de automatizaciones.

TRIGGERS:
    macro_tracker.meal_logged              — Al registrar una comida
    macro_tracker.daily_macro_threshold    — Al superar/no llegar a % del objetivo diario
    macro_tracker.goal_updated             — Al actualizar los objetivos nutricionales
    macro_tracker.no_entry_logged_today    — Si no hay entradas hoy a cierta hora
    macro_tracker.logging_streak           — Al cumplir N días consecutivos registrando

ACCIONES:
    macro_tracker.get_daily_summary        — Resumen de macros del día
    macro_tracker.get_weekly_stats         — Estadísticas semanales
    macro_tracker.get_goal_progress        — Progreso actual vs objetivos
    macro_tracker.log_meal                 — Registrar una comida
    macro_tracker.get_top_products         — Productos más usados en N días
"""


def register(registry) -> None:

    # ── TRIGGERS ──────────────────────────────────────────────────────────────

    registry.register_trigger(
        module_id="macro_tracker",
        trigger_id="meal_logged",
        label="Cuando se registra una comida",
        config_schema={
            "meal_type": {
                "type":     "enum[breakfast,morning_snack,lunch,afternoon_snack,dinner,other]",
                "label":    "Solo para este tipo de comida",
                "optional": True,
            },
            "min_energy_kcal": {
                "type":     "float",
                "label":    "Calorías mínimas de la entrada",
                "optional": True,
            },
            "max_energy_kcal": {
                "type":     "float",
                "label":    "Calorías máximas de la entrada",
                "optional": True,
            },
            "min_proteins_g": {
                "type":     "float",
                "label":    "Proteínas mínimas (g) de la entrada",
                "optional": True,
            },
            "nutriscore": {
                "type":     "enum[A,B,C,D,E]",
                "label":    "Solo para este Nutri-Score",
                "optional": True,
            },
            "product_name_contains": {
                "type":     "str",
                "label":    "Nombre del producto contiene (sin distinción de mayúsculas)",
                "optional": True,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.handle_meal_logged",
    )

    registry.register_trigger(
        module_id="macro_tracker",
        trigger_id="daily_macro_threshold",
        label="Cuando el total diario de un macro supera/baja de un porcentaje del objetivo",
        config_schema={
            "macro": {
                "type":  "enum[energy_kcal,proteins_g,carbohydrates_g,fat_g,fiber_g]",
                "label": "Macro a monitorizar",
            },
            "threshold_pct": {
                "type":    "float",
                "label":   "Porcentaje del objetivo (%)",
                "default": 100,
            },
            "direction": {
                "type":    "enum[above,below]",
                "label":   "Superar o no llegar",
                "default": "above",
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.handle_daily_macro_threshold",
    )

    registry.register_trigger(
        module_id="macro_tracker",
        trigger_id="goal_updated",
        label="Cuando se actualizan los objetivos nutricionales",
        config_schema={
            "macro_changed": {
                "type":     "enum[energy_kcal,proteins_g,carbohydrates_g,fat_g,fiber_g]",
                "label":    "Solo si cambia este macro",
                "optional": True,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.handle_goal_updated",
    )

    registry.register_trigger(
        module_id="macro_tracker",
        trigger_id="no_entry_logged_today",
        label="Si no se ha registrado ninguna comida hoy a cierta hora",
        config_schema={
            "check_hour": {
                "type":    "int",
                "label":   "Hora UTC a partir de la cual comprobar (0-23)",
                "default": 20,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.handle_no_entry_logged_today",
    )

    registry.register_trigger(
        module_id="macro_tracker",
        trigger_id="logging_streak",
        label="Al alcanzar exactamente N días consecutivos registrando comidas",
        config_schema={
            "streak_days": {
                "type":  "int",
                "label": "Días consecutivos objetivo (coincidencia exacta)",
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.handle_logging_streak",
    )

    # ── ACCIONES ──────────────────────────────────────────────────────────────

    registry.register_action(
        module_id="macro_tracker",
        action_id="get_daily_summary",
        label="Obtener resumen de macros del día",
        config_schema={
            "date_offset": {
                "type":    "int",
                "label":   "Desplazamiento en días (0=hoy, -1=ayer)",
                "default": 0,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.action_get_daily_summary",
    )

    registry.register_action(
        module_id="macro_tracker",
        action_id="get_weekly_stats",
        label="Obtener estadísticas semanales de macros",
        config_schema={
            "week_offset": {
                "type":    "int",
                "label":   "Desplazamiento en semanas (0=actual, -1=anterior)",
                "default": 0,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.action_get_weekly_stats",
    )

    registry.register_action(
        module_id="macro_tracker",
        action_id="get_goal_progress",
        label="Obtener progreso actual vs objetivos nutricionales",
        config_schema={},
        handler="app.modules.macro_tracker.automation_handlers.action_get_goal_progress",
    )

    registry.register_action(
        module_id="macro_tracker",
        action_id="log_meal",
        label="Registrar una comida",
        config_schema={
            "product_id": {
                "type":  "int",
                "label": "ID del producto",
            },
            "amount_g": {
                "type":  "float",
                "label": "Cantidad en gramos",
            },
            "meal_type": {
                "type":  "enum[breakfast,morning_snack,lunch,afternoon_snack,dinner,other]",
                "label": "Tipo de comida",
            },
            "date_offset": {
                "type":    "int",
                "label":   "Desplazamiento en días (0=hoy, -1=ayer)",
                "default": 0,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.action_log_meal",
    )

    registry.register_action(
        module_id="macro_tracker",
        action_id="get_top_products",
        label="Obtener productos más usados en los últimos N días",
        config_schema={
            "days": {
                "type":    "int",
                "label":   "Ventana de días a analizar",
                "default": 30,
            },
            "limit": {
                "type":    "int",
                "label":   "Número máximo de productos (máx. 10)",
                "default": 5,
            },
        },
        handler="app.modules.macro_tracker.automation_handlers.action_get_top_products",
    )
