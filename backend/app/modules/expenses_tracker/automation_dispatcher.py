"""
Dispatcher de automatizaciones para expenses_tracker.

Conecta los eventos del servicio y del scheduler con el motor de automatizaciones.
Este archivo es completamente opcional — si se elimina, los servicios siguen
funcionando y solo dejan de disparar automatizaciones.

TRIGGERS que despacha:
    expenses_tracker.large_expense_created     — Gasto creado por encima de umbral
    expenses_tracker.monthly_budget_exceeded   — Total mensual supera límite
    expenses_tracker.subscription_due_soon     — Suscripción vence en N días
    expenses_tracker.subscription_converted    — Suscripción vencida convertida en gasto real
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ExpensesAutomationDispatcher:

    def _find_and_execute(self, trigger_ref: str, payload: dict, user_id: int, db: Session) -> None:
        try:
            from app.modules.automations_engine.models.automation import Automation
            from app.modules.automations_engine.services.flow_executor import flow_executor
            from app.modules.automations_engine.services.execution_service import execution_service
            from datetime import datetime, timezone

            automations = db.query(Automation).filter(
                Automation.trigger_ref == trigger_ref,
                Automation.user_id     == user_id,
                Automation.is_active   == True,
            ).all()

            for automation in automations:
                try:
                    logger.info(
                        f"Disparando automatización '{automation.name}' "
                        f"(id={automation.id}) via {trigger_ref}"
                    )
                    execution = execution_service.create(automation.id, user_id, payload, db)
                    execution = execution_service.mark_running(execution, db)

                    result = flow_executor.execute(automation, payload, db, user_id)

                    if result["status"] == "success":
                        execution_service.mark_success(execution, result["node_logs"], db)
                    else:
                        execution_service.mark_failed(
                            execution, result.get("error", ""), result["node_logs"], db
                        )

                    automation.last_run_at = datetime.now(timezone.utc)
                    automation.run_count   = (automation.run_count or 0) + 1
                    db.commit()

                    logger.info(
                        f"Automatización '{automation.name}' terminó con status={result['status']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error ejecutando automatización '{automation.name}' "
                        f"(id={automation.id}): {e}"
                    )

        except ImportError:
            pass
        except Exception as e:
            logger.error(f"_find_and_execute({trigger_ref}) error: {e}")

    def on_large_expense_created(
        self, expense_id: int, amount: float, account: str, user_id: int, db: Session
    ) -> None:
        self._find_and_execute(
            trigger_ref="expenses_tracker.large_expense_created",
            payload={"expense_id": expense_id, "amount": amount, "account": account},
            user_id=user_id,
            db=db,
        )

    def on_subscription_converted(
        self,
        scheduled_id: int,
        expense_id: int,
        name: str,
        amount: float,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="expenses_tracker.subscription_converted",
            payload={
                "scheduled_id": scheduled_id,
                "expense_id":   expense_id,
                "name":         name,
                "amount":       amount,
            },
            user_id=user_id,
            db=db,
        )

    def on_monthly_budget_exceeded(
        self, total: float, month: str, account: str, user_id: int, db: Session
    ) -> None:
        self._find_and_execute(
            trigger_ref="expenses_tracker.monthly_budget_exceeded",
            payload={"total": total, "month": month, "account": account},
            user_id=user_id,
            db=db,
        )

    def on_subscription_due_soon(
        self,
        scheduled_id: int,
        name: str,
        amount: float,
        due_date: str,
        days_until: int,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="expenses_tracker.subscription_due_soon",
            payload={
                "scheduled_id": scheduled_id,
                "name":         name,
                "amount":       amount,
                "due_date":     due_date,
                "days_until":   days_until,
            },
            user_id=user_id,
            db=db,
        )


dispatcher = ExpensesAutomationDispatcher()
