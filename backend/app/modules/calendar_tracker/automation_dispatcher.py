"""
Dispatcher de automatizaciones para calendar_tracker.

Conecta los eventos del scheduler con el motor de automatizaciones.
Este archivo es completamente opcional — si se elimina, el scheduler
sigue funcionando y solo deja de disparar automatizaciones.

TRIGGERS que despacha:
    calendar_tracker.event_start            — Al iniciar un evento
    calendar_tracker.event_end              — Al finalizar un evento
    calendar_tracker.reminder_due           — Cuando vence un recordatorio
    calendar_tracker.no_events_in_window    — Cuando hay tiempo libre
    calendar_tracker.overdue_reminders_exist — Cuando hay recordatorios vencidos
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CalendarAutomationDispatcher:

    def _find_and_execute(self, trigger_ref: str, payload: dict, user_id: int, db: Session) -> None:
        try:
            from app.modules.automations_engine.models.automation import Automation
            from app.modules.automations_engine.services.flow_executor import flow_executor
            from app.modules.automations_engine.services.execution_service import execution_service

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

    def on_event_start(self, event_id: int, user_id: int, db: Session) -> None:
        self._find_and_execute(
            trigger_ref="calendar_tracker.event_start",
            payload={"event_id": event_id},
            user_id=user_id,
            db=db,
        )

    def on_event_end(self, event_id: int, user_id: int, db: Session) -> None:
        self._find_and_execute(
            trigger_ref="calendar_tracker.event_end",
            payload={"event_id": event_id},
            user_id=user_id,
            db=db,
        )

    def on_reminder_due(self, reminder_id: int, user_id: int, db: Session) -> None:
        self._find_and_execute(
            trigger_ref="calendar_tracker.reminder_due",
            payload={"reminder_id": reminder_id},
            user_id=user_id,
            db=db,
        )

    def on_no_events_in_window(self, user_id: int, db: Session) -> None:
        from app.modules.calendar_tracker.models.event import Event

        now = datetime.now(timezone.utc)
        end = now + timedelta(hours=2)

        events_in_window = db.query(Event).filter(
            Event.user_id      == user_id,
            Event.is_cancelled == False,
            Event.start_at     <= end,
            Event.end_at       >= now,
        ).count()

        if events_in_window > 0:
            return  # hay eventos en la ventana — no disparar

        self._find_and_execute(
            trigger_ref="calendar_tracker.no_events_in_window",
            payload={},
            user_id=user_id,
            db=db,
        )

    def on_overdue_reminders_exist(self, user_id: int, db: Session) -> None:
        self._find_and_execute(
            trigger_ref="calendar_tracker.overdue_reminders_exist",
            payload={},
            user_id=user_id,
            db=db,
        )


dispatcher = CalendarAutomationDispatcher()