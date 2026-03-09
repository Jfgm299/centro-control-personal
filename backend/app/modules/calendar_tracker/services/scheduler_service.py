"""
Scheduler de calendar_tracker.
Detecta eventos que empiezan/terminan y recordatorios vencidos,
envía notificaciones y dispara automatizaciones.

Se ejecuta cada 60 segundos en background via APScheduler.
Es completamente independiente del motor de automatizaciones —
si automation_dispatcher.py no existe, el scheduler sigue funcionando.
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from ..models.event import Event
from ..models.reminder import Reminder
from ..enums import ReminderStatus
from .notification_service import NotificationService

logger = logging.getLogger(__name__)
notification_service = NotificationService()

# ── Deduplicación en memoria ──────────────────────────────────────────────────
# Evita disparar el mismo trigger dos veces para el mismo objeto en poco tiempo.
# Estructura: {(object_id, trigger_ref): datetime_of_last_dispatch}
_dispatch_cache: dict[tuple, datetime] = {}
_DEDUP_TTL = timedelta(minutes=5)


def _already_dispatched(object_id: int, trigger_ref: str) -> bool:
    key = (object_id, trigger_ref)
    last = _dispatch_cache.get(key)
    if last and (datetime.now(timezone.utc) - last) < _DEDUP_TTL:
        return True
    return False


def _mark_dispatched(object_id: int, trigger_ref: str) -> None:
    key = (object_id, trigger_ref)
    _dispatch_cache[key] = datetime.now(timezone.utc)
    # Limpiar entradas expiradas para no crecer indefinidamente
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _dispatch_cache.items() if (now - v) >= _DEDUP_TTL]
    for k in expired:
        del _dispatch_cache[k]


def _get_db() -> Session:
    return SessionLocal()


def _try_dispatch(method_name: str, *args, **kwargs) -> None:
    """
    Llama al dispatcher de automatizaciones si existe.
    Si el módulo no está instalado o falla, se ignora silenciosamente.
    """
    try:
        from ..automation_dispatcher import dispatcher
        getattr(dispatcher, method_name)(*args, **kwargs)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"automation_dispatcher.{method_name} falló: {e}")


def job_process_notifications() -> None:
    """Envía notificaciones FCM pendientes cuyo trigger_at ya ha llegado."""
    db = _get_db()
    try:
        pending = notification_service.get_pending_due(db)
        for notification in pending:
            try:
                # TODO: integrar con Firebase cuando esté listo
                notification_service.mark_sent(db, notification)
                logger.info(f"Notificación {notification.id} enviada — '{notification.title}'")
            except Exception as e:
                notification_service.mark_failed(db, notification)
                logger.error(f"Notificación {notification.id} falló: {e}")
    except Exception as e:
        logger.error(f"job_process_notifications error: {e}")
    finally:
        db.close()


def job_check_event_starts() -> None:
    """
    Detecta eventos que empiezan en la ventana [now-60s, now+60s]
    y dispara automatizaciones suscritas a calendar_tracker.event_start.
    La ventana ampliada (+60s hacia adelante) garantiza que ningún evento
    quede fuera por timing del scheduler. La deduplicación evita dobles disparos.
    """
    db = _get_db()
    try:
        now          = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=60)
        window_end   = now + timedelta(seconds=60)

        events = db.query(Event).filter(
            Event.is_cancelled == False,
            Event.start_at >= window_start,
            Event.start_at <= window_end,
        ).all()

        for event in events:
            if _already_dispatched(event.id, "event_start"):
                continue
            logger.info(f"Evento iniciando: '{event.title}' (id={event.id}, user={event.user_id})")
            _mark_dispatched(event.id, "event_start")
            _try_dispatch("on_event_start", event_id=event.id, user_id=event.user_id, db=db)

    except Exception as e:
        logger.error(f"job_check_event_starts error: {e}")
    finally:
        db.close()


def job_check_event_ends() -> None:
    """
    Detecta eventos que terminan en la ventana [now-60s, now+60s]
    y dispara automatizaciones suscritas a calendar_tracker.event_end.
    """
    db = _get_db()
    try:
        now          = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=60)
        window_end   = now + timedelta(seconds=60)

        events = db.query(Event).filter(
            Event.is_cancelled == False,
            Event.end_at >= window_start,
            Event.end_at <= window_end,
        ).all()

        for event in events:
            if _already_dispatched(event.id, "event_end"):
                continue
            logger.info(f"Evento terminando: '{event.title}' (id={event.id}, user={event.user_id})")
            _mark_dispatched(event.id, "event_end")
            _try_dispatch("on_event_end", event_id=event.id, user_id=event.user_id, db=db)

    except Exception as e:
        logger.error(f"job_check_event_ends error: {e}")
    finally:
        db.close()


def job_check_reminders_due() -> None:
    """
    Detecta recordatorios que vencen hoy y aún están pendientes,
    y dispara automatizaciones suscritas a calendar_tracker.reminder_due.
    La deduplicación evita disparar el mismo recordatorio múltiples veces al día.
    """
    db = _get_db()
    try:
        today = datetime.now(timezone.utc).date()

        reminders = db.query(Reminder).filter(
            Reminder.status   == ReminderStatus.PENDING,
            Reminder.due_date == today,
        ).all()

        for reminder in reminders:
            if _already_dispatched(reminder.id, "reminder_due"):
                continue
            logger.info(f"Recordatorio vencido: '{reminder.title}' (id={reminder.id}, user={reminder.user_id})")
            _mark_dispatched(reminder.id, "reminder_due")
            _try_dispatch("on_reminder_due", reminder_id=reminder.id, user_id=reminder.user_id, db=db)

    except Exception as e:
        logger.error(f"job_check_reminders_due error: {e}")
    finally:
        db.close()


def job_check_free_windows() -> None:
    """
    Detecta ventanas de tiempo libre y dispara automatizaciones
    suscritas a calendar_tracker.no_events_in_window.
    Se ejecuta cada 30 minutos.
    """
    db = _get_db()
    try:
        from app.modules.automations_engine.models.automation import Automation

        user_ids = [
            row[0] for row in db.query(Automation.user_id).filter(
                Automation.trigger_ref == "calendar_tracker.no_events_in_window",
                Automation.is_active   == True,
            ).distinct().all()
        ]

        for user_id in user_ids:
            _try_dispatch("on_no_events_in_window", user_id=user_id, db=db)

    except Exception as e:
        logger.error(f"job_check_free_windows error: {e}")
    finally:
        db.close()


def job_check_overdue_reminders() -> None:
    """
    Detecta si existen recordatorios vencidos (pasados) pendientes
    y dispara automatizaciones suscritas a calendar_tracker.overdue_reminders_exist.
    Se ejecuta una vez al día.
    """
    db = _get_db()
    try:
        from sqlalchemy import distinct
        today    = datetime.now(timezone.utc).date()
        user_ids = [
            row[0] for row in db.query(distinct(Reminder.user_id)).filter(
                Reminder.status   == ReminderStatus.PENDING,
                Reminder.due_date <  today,
            ).all()
        ]

        for user_id in user_ids:
            logger.info(f"Recordatorios vencidos detectados para user {user_id}")
            _try_dispatch("on_overdue_reminders_exist", user_id=user_id, db=db)

    except Exception as e:
        logger.error(f"job_check_overdue_reminders error: {e}")
    finally:
        db.close()

def job_sync_calendars() -> None:
    db = _get_db()
    try:
        from app.modules.calendar_tracker.models.calendar_sync import CalendarConnection
        from app.modules.calendar_tracker.services.sync_service import sync_service

        connections = db.query(CalendarConnection).filter(
            CalendarConnection.is_active == True
        ).all()

        for connection in connections:
            try:
                sync_service.sync(connection, db)
            except Exception as e:
                logger.error(f"job_sync_calendars error para connection {connection.id}: {e}")

    except Exception as e:
        logger.error(f"job_sync_calendars error: {e}")
    finally:
        db.close()