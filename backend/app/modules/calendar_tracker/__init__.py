from .routers.calendar_router import router
from .routers.sync_router import router as sync_router
from .handlers import register_exception_handlers as register_handlers

router.include_router(sync_router)

TAGS = [
    {"name": "Calendar",    "description": "Gestion de eventos, recordatorios y rutinas"},
    {"name": "Reminders",   "description": "Recordatorios pendientes de asignar"},
    {"name": "Routines",    "description": "Rutinas recurrentes con patron override"},
    {"name": "Categories",  "description": "Categorias personalizadas con color"},
]

TAG_GROUP = {
    "name": "Calendar",
    "tags": ["Calendar", "Reminders", "Routines", "Categories"],
}


def start_calendar_scheduler() -> None:
    from apscheduler.schedulers.background import BackgroundScheduler
    import logging as _logging
    from .services.scheduler_service import (
        job_process_notifications,
        job_check_event_starts,
        job_check_event_ends,
        job_check_reminders_due,
        job_check_free_windows,
        job_check_overdue_reminders,
        job_sync_calendars,
    )

    scheduler = BackgroundScheduler(timezone="UTC")

    # Notificaciones — cada 60 segundos
    scheduler.add_job(job_process_notifications,  "interval", seconds=60,   id="calendar_notifications")
    # Eventos que empiezan — cada 60 segundos
    scheduler.add_job(job_check_event_starts,     "interval", seconds=60,   id="calendar_event_starts")
    # Eventos que terminan — cada 60 segundos
    scheduler.add_job(job_check_event_ends,       "interval", seconds=60,   id="calendar_event_ends")
    # Recordatorios que vencen hoy — cada 5 minutos
    scheduler.add_job(job_check_reminders_due,    "interval", minutes=5,    id="calendar_reminders_due")
    # Ventanas de tiempo libre — cada 30 minutos
    scheduler.add_job(job_check_free_windows,     "interval", minutes=30,   id="calendar_free_windows")
    # Recordatorios vencidos acumulados — una vez al día a las 9:00 UTC
    scheduler.add_job(job_check_overdue_reminders,"cron",     hour=9,       id="calendar_overdue_reminders")
    # Sincronización con Google/Apple Calendar — cada 10 minutos
    scheduler.add_job(job_sync_calendars,         "interval", minutes=10,   id="calendar_sync")

    scheduler.start()
    _logging.getLogger(__name__).info("✅ Calendar scheduler iniciado")


__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP", "start_calendar_scheduler"]
