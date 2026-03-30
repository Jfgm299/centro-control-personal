"""
Dispatcher de automatizaciones para flights_tracker.

Conecta los eventos del servicio (add_flight, refresh_flight) y del scheduler
con el motor de automatizaciones.
Este archivo es completamente opcional — si se elimina, los servicios siguen
funcionando y solo dejan de disparar automatizaciones.

TRIGGERS que despacha:
    flights_tracker.flight_added           — Vuelo registrado
    flights_tracker.flight_status_changed  — Estado del vuelo cambió
    flights_tracker.flight_departing_soon  — Vuelo sale en N horas
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FlightsAutomationDispatcher:

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

    def on_flight_added(
        self,
        flight_id: int,
        flight_number: str,
        flight_date: str,
        status: str,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="flights_tracker.flight_added",
            payload={
                "flight_id":     flight_id,
                "flight_number": flight_number,
                "flight_date":   flight_date,
                "status":        status,
            },
            user_id=user_id,
            db=db,
        )

    def on_flight_status_changed(
        self,
        flight_id: int,
        old_status: str,
        new_status: str,
        flight_dict: dict,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="flights_tracker.flight_status_changed",
            payload={
                "flight_id":  flight_id,
                "old_status": old_status,
                "new_status": new_status,
                "flight":     flight_dict,
            },
            user_id=user_id,
            db=db,
        )

    def on_flight_departing_soon(
        self,
        flight_id: int,
        hours_until_departure: float,
        flight_dict: dict,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="flights_tracker.flight_departing_soon",
            payload={
                "flight_id":             flight_id,
                "hours_until_departure": hours_until_departure,
                "flight":                flight_dict,
            },
            user_id=user_id,
            db=db,
        )


dispatcher = FlightsAutomationDispatcher()
