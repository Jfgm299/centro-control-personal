"""
Scheduler de gym_tracker.
Detecta usuarios con inactividad de entrenamiento y dispara automatizaciones.

Se ejecuta una vez al día via APScheduler (09:00 UTC).
Es completamente independiente del motor de automatizaciones —
si automation_dispatcher.py no existe, el scheduler sigue funcionando.
"""
import logging
from datetime import datetime, timezone

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# ── Deduplicación en memoria ──────────────────────────────────────────────────
# Evita disparar el mismo trigger dos veces en el mismo día para el mismo usuario.
# Clave: (user_id, "YYYY-MM-DD")
_inactivity_fired: set[tuple] = set()


def _get_db():
    return SessionLocal()


def job_check_workout_inactivity() -> None:
    """
    Itera todas las automations activas con trigger_ref=gym_tracker.workout_inactivity.
    Para cada usuario distinto, llama dispatcher.on_workout_inactivity_check().
    Deduplicación: (user_id, "YYYY-MM-DD") — una vez por día por usuario.

    NOTA: No llamar directamente en tests — usa SessionLocal() apuntando al DB
    de dev (puerto 5432). En tests, llamar dispatcher.on_workout_inactivity_check()
    con la sesión de test directamente.
    """
    db = _get_db()
    try:
        from app.modules.automations_engine.models.automation import Automation

        today     = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        processed: set = set()  # user_ids ya procesados en esta ejecución

        automations = db.query(Automation).filter(
            Automation.trigger_ref == "gym_tracker.workout_inactivity",
            Automation.is_active   == True,
        ).all()

        for automation in automations:
            user_id = automation.user_id

            # Evitar procesar el mismo usuario dos veces en la misma ejecución
            if user_id in processed:
                continue

            # Deduplicación entre ejecuciones del día
            dedup_key = (user_id, today)
            if dedup_key in _inactivity_fired:
                continue

            processed.add(user_id)
            _inactivity_fired.add(dedup_key)

            try:
                from .automation_dispatcher import dispatcher
                dispatcher.on_workout_inactivity_check(user_id=user_id, db=db)
            except ImportError:
                pass
            except Exception as e:
                logger.warning(
                    f"automation_dispatcher.on_workout_inactivity_check falló "
                    f"(user_id={user_id}): {e}"
                )

    except Exception as e:
        logger.error(f"job_check_workout_inactivity error: {e}")
    finally:
        db.close()


def start_gym_scheduler() -> None:
    """
    Arranca el scheduler de gym_tracker.
    Debe llamarse desde el startup_event de FastAPI (nunca en import-time).
    """
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        job_check_workout_inactivity,
        "cron",
        hour=9,
        minute=0,
        id="gym_workout_inactivity",
    )
    scheduler.start()
    logger.info("Gym scheduler iniciado (inactividad @ 09:00 UTC)")
