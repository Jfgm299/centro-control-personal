"""
Scheduler del automations_engine para triggers de tipo CRON.

Detecta automations activas con trigger_type=CRON, evalúa si deben ejecutarse
según su schedule (schedule_once o schedule_interval), y las lanza via flow_executor.

Se ejecuta cada 60 segundos en background via APScheduler.
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

_SYSTEM_CRON_TRIGGERS = {"system.schedule_once", "system.schedule_interval"}


def _get_trigger_config(automation) -> dict | None:
    """Extrae el config del nodo trigger del flow JSON."""
    for node in automation.flow.get("nodes", []):
        if node.get("type") == "trigger":
            return node.get("config", {})
    return None


def _should_run_once(config: dict, last_run_at) -> bool:
    """schedule_once: ejecutar si run_at <= now y nunca se ha ejecutado."""
    if last_run_at is not None:
        return False
    run_at_str = config.get("run_at")
    if not run_at_str:
        return False
    try:
        run_at = datetime.fromisoformat(run_at_str.replace("Z", "+00:00"))
        return run_at <= datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def _should_run_interval(config: dict, last_run_at) -> bool:
    """schedule_interval: ejecutar si ha pasado el intervalo desde el último run."""
    interval_value = config.get("interval_value", 30)
    interval_unit  = config.get("interval_unit", "minutes")

    if interval_unit == "minutes":
        delta = timedelta(minutes=interval_value)
    elif interval_unit == "hours":
        delta = timedelta(hours=interval_value)
    elif interval_unit == "days":
        delta = timedelta(days=interval_value)
    else:
        return False

    now = datetime.now(timezone.utc)

    active_from  = config.get("active_from")
    active_until = config.get("active_until")
    if active_from and active_until:
        try:
            from_h, from_m   = (int(x) for x in active_from.split(":"))
            until_h, until_m = (int(x) for x in active_until.split(":"))
            now_minutes   = now.hour * 60 + now.minute
            from_minutes  = from_h * 60 + from_m
            until_minutes = until_h * 60 + until_m
            if not (from_minutes <= now_minutes <= until_minutes):
                return False
        except (ValueError, TypeError):
            pass

    if last_run_at is None:
        return True

    return (now - last_run_at) >= delta


def _execute_automation(automation, db: Session) -> None:
    from .flow_executor import flow_executor
    from .execution_service import execution_service

    execution = execution_service.create(automation.id, automation.user_id, {}, db)
    execution = execution_service.mark_running(execution, db)

    try:
        result = flow_executor.execute(automation, payload={}, db=db, user_id=automation.user_id)
        if result["status"] == "failed":
            execution_service.mark_failed(execution, result.get("error", ""), result["node_logs"], db)
        else:
            execution_service.mark_success(execution, result["node_logs"], db)
    except Exception as e:
        execution_service.mark_failed(execution, str(e), [], db)
        raise


def start_cron_scheduler() -> None:
    """Arranca el scheduler de CRON del automations_engine."""
    from apscheduler.schedulers.background import BackgroundScheduler
    import logging

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(job_check_cron_automations, "interval", seconds=60, id="cron_automations")
    scheduler.start()
    logging.getLogger(__name__).info("✅ Automations CRON scheduler iniciado")


def job_check_cron_automations() -> None:
    """Evalúa y ejecuta automations con trigger_type=CRON según su schedule."""
    from ..models.automation import Automation
    from ..enums import AutomationTriggerType

    db = SessionLocal()
    try:
        automations = db.query(Automation).filter(
            Automation.trigger_type == AutomationTriggerType.CRON,
            Automation.is_active    == True,
        ).all()

        for automation in automations:
            try:
                config = _get_trigger_config(automation)
                if config is None:
                    continue

                trigger_id = config.get("trigger_id")
                if trigger_id not in _SYSTEM_CRON_TRIGGERS:
                    continue

                if trigger_id == "system.schedule_once":
                    should_run = _should_run_once(config, automation.last_run_at)
                else:
                    should_run = _should_run_interval(config, automation.last_run_at)

                if not should_run:
                    continue

                logger.info(
                    f"Ejecutando automation CRON '{automation.name}' "
                    f"(id={automation.id}, trigger={trigger_id})"
                )

                _execute_automation(automation, db)

                automation.last_run_at = datetime.now(timezone.utc)
                automation.run_count   = (automation.run_count or 0) + 1
                if trigger_id == "system.schedule_once":
                    automation.is_active = False
                db.commit()

            except Exception as e:
                logger.error(f"Error al procesar automation CRON id={automation.id}: {e}")
                db.rollback()

    except Exception as e:
        logger.error(f"job_check_cron_automations error: {e}")
    finally:
        db.close()
