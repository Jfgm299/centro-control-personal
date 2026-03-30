"""
Triggers y acciones que expenses_tracker expone al motor de automatizaciones.

TRIGGERS:
    expenses_tracker.large_expense_created     — Cuando se crea un gasto por encima de un umbral
    expenses_tracker.monthly_budget_exceeded   — Cuando el total mensual supera un límite
    expenses_tracker.subscription_due_soon     — Cuando una suscripción vence en N días
    expenses_tracker.subscription_converted    — Cuando una suscripción vencida se convierte en gasto real

ACCIONES:
    expenses_tracker.create_expense            — Crear un gasto puntual
    expenses_tracker.get_monthly_summary       — Obtener totales mensuales por cuenta
    expenses_tracker.get_upcoming_subscriptions — Listar suscripciones activas próximas
"""


def register(registry) -> None:

    # ── TRIGGERS ──────────────────────────────────────────────────────────────

    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="large_expense_created",
        label="Cuando se crea un gasto grande",
        config_schema={
            "min_amount": {"type": "float", "label": "Importe mínimo para disparar", "default": 100.0},
            "account":    {"type": "enum[Revolut,Imagin]", "label": "Solo esta cuenta", "optional": True},
        },
        handler="app.modules.expenses_tracker.automation_handlers.handle_large_expense_created",
    )

    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="monthly_budget_exceeded",
        label="Cuando se supera el presupuesto mensual",
        config_schema={
            "limit":   {"type": "float",                   "label": "Límite mensual en €",  "default": 1000.0},
            "account": {"type": "enum[Revolut,Imagin,all]","label": "Cuenta a controlar",   "default": "all"},
        },
        handler="app.modules.expenses_tracker.automation_handlers.handle_monthly_budget_exceeded",
    )

    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="subscription_due_soon",
        label="Cuando una suscripción vence pronto",
        config_schema={
            "days_ahead": {"type": "int", "label": "Días de antelación", "default": 3},
        },
        handler="app.modules.expenses_tracker.automation_handlers.handle_subscription_due_soon",
    )

    registry.register_trigger(
        module_id="expenses_tracker",
        trigger_id="subscription_converted",
        label="Cuando una suscripción vencida se convierte en gasto",
        config_schema={},
        handler="app.modules.expenses_tracker.automation_handlers.handle_subscription_converted",
    )

    # ── ACCIONES ──────────────────────────────────────────────────────────────

    registry.register_action(
        module_id="expenses_tracker",
        action_id="create_expense",
        label="Crear un gasto puntual",
        config_schema={
            "name":    {"type": "str",                    "label": "Nombre del gasto"},
            "amount":  {"type": "float",                  "label": "Importe en €"},
            "account": {"type": "enum[Revolut,Imagin]",   "label": "Cuenta", "default": "Revolut"},
        },
        handler="app.modules.expenses_tracker.automation_handlers.action_create_expense",
    )

    registry.register_action(
        module_id="expenses_tracker",
        action_id="get_monthly_summary",
        label="Obtener resumen mensual de gastos",
        config_schema={
            "month_offset": {"type": "int", "label": "Mes (0=actual, -1=anterior)", "default": 0},
        },
        handler="app.modules.expenses_tracker.automation_handlers.action_get_monthly_summary",
    )

    registry.register_action(
        module_id="expenses_tracker",
        action_id="get_upcoming_subscriptions",
        label="Listar suscripciones próximas",
        config_schema={
            "days_ahead": {"type": "int", "label": "Días hacia adelante", "default": 30},
        },
        handler="app.modules.expenses_tracker.automation_handlers.action_get_upcoming_subscriptions",
    )
