from .flight_router import router
from .handlers import register_exception_handlers as register_handlers  # ← añadir

TAGS = [
    {"name": "Flights", "description": "Registro y tracking de vuelos"},
]
TAG_GROUP = {
    "name": "Flights",
    "tags": ["Flights"],
}


def start_flights_scheduler() -> None:
    from apscheduler.schedulers.background import BackgroundScheduler
    import logging as _logging
    from .scheduler_service import job_check_flight_departing_soon

    scheduler = BackgroundScheduler(timezone="UTC")

    # Vuelos próximos a salir — cada hora en punto
    scheduler.add_job(job_check_flight_departing_soon, "cron", minute=0, id="flights_departing_soon")

    scheduler.start()
    _logging.getLogger(__name__).info("✅ Flights scheduler iniciado")


__all__ = ["router", "register_handlers", "TAGS", "TAG_GROUP", "start_flights_scheduler"]