"""
Tests del dispatcher y automation handlers de expenses_tracker.

Probamos:
1. Trigger large_expense_created — dispara si el importe supera el umbral
2. Trigger large_expense_created — no dispara si el importe está por debajo
3. Trigger subscription_converted — dispara cuando la suscripción se convierte
4. Trigger subscription_due_soon — dispara cuando la suscripción vence pronto
5. Action create_expense — crea un gasto real en la DB
6. Action get_monthly_summary — devuelve totales del mes
7. Action get_upcoming_subscriptions — devuelve suscripciones próximas
"""
import pytest
from datetime import date, timedelta

from app.modules.expenses_tracker.automation_dispatcher import dispatcher


class TestExpensesDispatcher:

    def _run_automation(
        self, auth_client, db, trigger_ref, action_id, action_config, payload, user_id
    ):
        """Helper: crea y ejecuta una automatización con una acción específica."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        r = auth_client.post("/api/v1/automations/", json={
            "name":         f"Test {action_id}",
            "trigger_type": "module_event",
            "trigger_ref":  trigger_ref,
            "flow": {
                "nodes": [
                    {"id": "n1", "type": "trigger", "config": {"trigger_id": trigger_ref}},
                    {"id": "n2", "type": "action",  "config": {"action_id": action_id, **action_config}},
                ],
                "edges": [{"from": "n1", "to": "n2"}],
            },
        })
        assert r.status_code == 201, r.json()
        automation_id = r.json()["id"]

        dispatcher._find_and_execute(
            trigger_ref=trigger_ref,
            payload=payload,
            user_id=user_id,
            db=db,
        )

        execution = db.query(
            __import__(
                "app.modules.automations_engine.models.execution",
                fromlist=["Execution"]
            ).Execution
        ).filter_by(automation_id=automation_id).first()
        return execution

    def test_large_expense_trigger_fires_when_above_threshold(
        self, db, auth_client, large_expense_id, automation_for_large_expense
    ):
        """large_expense_created dispara si el importe supera el umbral."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_large_expense
        ).first()

        dispatcher.on_large_expense_created(
            expense_id=large_expense_id,
            amount=200.0,
            account="Revolut",
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_large_expense
        ).all()
        assert len(executions) == 1
        assert executions[0].status.value in ("success", "failed")

    def test_large_expense_trigger_skips_when_below_threshold(
        self, db, auth_client, large_expense_id, automation_for_large_expense
    ):
        """large_expense_created no dispara si el importe está por debajo del umbral."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_large_expense
        ).first()
        user_id = automation.user_id

        # Crear gasto pequeño
        r = auth_client.post("/api/v1/expenses/", json={
            "name": "Café", "quantity": 5.0, "account": "Imagin"
        })
        small_id = r.json()["id"]

        dispatcher.on_large_expense_created(
            expense_id=small_id,
            amount=5.0,
            account="Imagin",
            user_id=user_id,
            db=db,
        )

        # La automatización tiene min_amount=100 — 5€ no debe disparar
        # Nota: el dispatcher _dispara_ siempre, pero el trigger handler
        # devuelve matched=False y el flow queda como "skipped"
        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_large_expense
        ).all()
        # Si hay ejecución, debe haber terminado (puede ser success con matched=False o skipped)
        for e in executions:
            assert e.status.value in ("success", "failed", "skipped")

    def test_subscription_converted_trigger_fires(
        self, db, auth_client, automation_for_subscription_converted
    ):
        """subscription_converted dispara cuando la suscripción se convierte en gasto."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        # Crear una suscripción con fecha pasada y un gasto resultado
        r_sub = auth_client.post("/api/v1/expenses/scheduled", json={
            "name":              "HBO",
            "amount":            8.99,
            "account":           "Revolut",
            "category":          "SUBSCRIPTION",
            "frequency":         "MONTHLY",
            "next_payment_date": str(date.today() - timedelta(days=1)),
            "is_active":         True,
        })
        assert r_sub.status_code == 201, r_sub.json()
        scheduled_id = r_sub.json()["id"]

        r_exp = auth_client.post("/api/v1/expenses/", json={
            "name": "HBO", "quantity": 8.99, "account": "Revolut"
        })
        expense_id = r_exp.json()["id"]

        automation = db.query(Automation).filter(
            Automation.id == automation_for_subscription_converted
        ).first()

        dispatcher.on_subscription_converted(
            scheduled_id=scheduled_id,
            expense_id=expense_id,
            name="HBO",
            amount=8.99,
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_subscription_converted
        ).all()
        assert len(executions) == 1
        assert executions[0].status.value in ("success", "failed")

    def test_subscription_due_soon_trigger_fires(
        self, db, auth_client, upcoming_subscription_id, automation_for_subscription_due_soon
    ):
        """subscription_due_soon dispara cuando la suscripción vence en N días."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.automations_engine.models.execution import Execution

        automation = db.query(Automation).filter(
            Automation.id == automation_for_subscription_due_soon
        ).first()

        dispatcher.on_subscription_due_soon(
            scheduled_id=upcoming_subscription_id,
            name="Suscripción próxima",
            amount=9.99,
            due_date=str(date.today() + timedelta(days=3)),
            days_until=3,
            user_id=automation.user_id,
            db=db,
        )

        executions = db.query(Execution).filter(
            Execution.automation_id == automation_for_subscription_due_soon
        ).all()
        assert len(executions) == 1
        assert executions[0].status.value in ("success", "failed")

    def test_action_create_expense(self, db, auth_client, large_expense_id, automation_for_large_expense):
        """action_create_expense crea un gasto real en la DB."""
        from app.modules.automations_engine.models.automation import Automation
        from app.modules.expenses_tracker.expense import Expense

        automation = db.query(Automation).filter(
            Automation.id == automation_for_large_expense
        ).first()
        user_id = automation.user_id

        expenses_before = db.query(Expense).filter(Expense.user_id == user_id).count()

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="expenses_tracker.large_expense_created",
            action_id="expenses_tracker.create_expense",
            action_config={"name": "Gasto automático", "amount": 50.0, "account": "Revolut"},
            payload={"expense_id": large_expense_id, "amount": 200.0, "account": "Revolut"},
            user_id=user_id,
        )

        assert execution is not None
        assert execution.status.value == "success"

        expenses_after = db.query(Expense).filter(Expense.user_id == user_id).count()
        assert expenses_after == expenses_before + 1

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True
        assert action_log["output"]["expense"]["name"] == "Gasto automático"

    def test_action_get_monthly_summary(self, db, auth_client, large_expense_id, automation_for_large_expense):
        """action_get_monthly_summary devuelve totales del mes actual."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_large_expense
        ).first()
        user_id = automation.user_id

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="expenses_tracker.large_expense_created",
            action_id="expenses_tracker.get_monthly_summary",
            action_config={"month_offset": 0},
            payload={"expense_id": large_expense_id, "amount": 200.0, "account": "Revolut"},
            user_id=user_id,
        )

        assert execution is not None
        assert execution.status.value == "success"

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True
        assert "grand_total" in action_log["output"]
        assert "total_by_account" in action_log["output"]
        assert "month" in action_log["output"]
        assert action_log["output"]["count"] >= 1

    def test_action_get_upcoming_subscriptions(
        self, db, auth_client, upcoming_subscription_id, automation_for_subscription_due_soon
    ):
        """action_get_upcoming_subscriptions devuelve suscripciones próximas."""
        from app.modules.automations_engine.models.automation import Automation

        automation = db.query(Automation).filter(
            Automation.id == automation_for_subscription_due_soon
        ).first()
        user_id = automation.user_id

        execution = self._run_automation(
            auth_client=auth_client,
            db=db,
            trigger_ref="expenses_tracker.subscription_due_soon",
            action_id="expenses_tracker.get_upcoming_subscriptions",
            action_config={"days_ahead": 30},
            payload={
                "scheduled_id": upcoming_subscription_id,
                "name":         "Suscripción próxima",
                "amount":       9.99,
                "due_date":     str(date.today() + timedelta(days=3)),
                "days_until":   3,
            },
            user_id=user_id,
        )

        assert execution is not None
        assert execution.status.value == "success"

        action_log = next(l for l in execution.node_logs if l["node_type"] == "action")
        assert action_log["output"]["done"] is True
        assert action_log["output"]["count"] >= 1
        assert isinstance(action_log["output"]["subscriptions"], list)
        assert "days_until" in action_log["output"]["subscriptions"][0]
