"""
Dispatcher de automatizaciones para gym_tracker.

Conecta los eventos del servicio (workout_service, set_service, body_measurement_service)
y del scheduler con el motor de automatizaciones.
Este archivo es completamente opcional — si se elimina, los servicios siguen
funcionando y solo dejan de disparar automatizaciones.

TRIGGERS que despacha:
    gym_tracker.workout_started             — Workout iniciado
    gym_tracker.workout_ended               — Workout terminado
    gym_tracker.personal_record_weight      — Récord personal de peso
    gym_tracker.body_measurement_recorded   — Medición corporal registrada
    gym_tracker.workout_inactivity          — N días sin entrenar
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class GymAutomationDispatcher:

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

    def on_workout_started(
        self,
        workout_id: int,
        started_at: str,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="gym_tracker.workout_started",
            payload={
                "workout_id": workout_id,
                "started_at": started_at,
            },
            user_id=user_id,
            db=db,
        )

    def on_workout_ended(
        self,
        workout_id: int,
        duration_minutes,
        total_exercises: int,
        total_sets: int,
        muscle_groups: list,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="gym_tracker.workout_ended",
            payload={
                "workout_id":       workout_id,
                "duration_minutes": duration_minutes,
                "total_exercises":  total_exercises,
                "total_sets":       total_sets,
                "muscle_groups":    muscle_groups,
            },
            user_id=user_id,
            db=db,
        )

    def on_personal_record_weight(
        self,
        exercise_name: str,
        new_weight_kg: float,
        previous_record_kg,  # float | None
        reps,                # int | None
        workout_id: int,
        set_id: int,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="gym_tracker.personal_record_weight",
            payload={
                "exercise_name":      exercise_name,
                "new_weight_kg":      new_weight_kg,
                "previous_record_kg": previous_record_kg,
                "reps":               reps,
                "workout_id":         workout_id,
                "set_id":             set_id,
            },
            user_id=user_id,
            db=db,
        )

    def on_body_measurement_recorded(
        self,
        measurement_id: int,
        weight_kg,           # float | None
        body_fat_percentage, # float | None
        recorded_at: str,
        user_id: int,
        db: Session,
    ) -> None:
        self._find_and_execute(
            trigger_ref="gym_tracker.body_measurement_recorded",
            payload={
                "measurement_id":      measurement_id,
                "weight_kg":           weight_kg,
                "body_fat_percentage": body_fat_percentage,
                "recorded_at":         recorded_at,
            },
            user_id=user_id,
            db=db,
        )

    def on_workout_inactivity_check(self, user_id: int, db: Session) -> None:
        """
        Llamado por el scheduler para verificar la inactividad de un usuario.
        Computa days_since_last_workout y llama _find_and_execute con ese payload.
        El handler (handle_workout_inactivity) evalúa el threshold contra config.
        """
        from datetime import datetime, timezone
        from .models.workout import Workout

        last_workout = (
            db.query(Workout)
            .filter(Workout.user_id == user_id)
            .order_by(Workout.started_at.desc())
            .first()
        )

        if last_workout and last_workout.started_at:
            now     = datetime.now(timezone.utc)
            started = last_workout.started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            days_since = (now - started).days
            last_date  = started.date().isoformat()
        else:
            days_since = None
            last_date  = None

        self._find_and_execute(
            trigger_ref="gym_tracker.workout_inactivity",
            payload={
                "days_since_last_workout": days_since,
                "last_workout_date":       last_date,
            },
            user_id=user_id,
            db=db,
        )


dispatcher = GymAutomationDispatcher()
