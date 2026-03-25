"""
Scheduler de flights_tracker.
Detecta vuelos próximos a salir y dispara automatizaciones.

Se ejecuta una vez por hora via APScheduler.
Es completamente independiente del motor de automatizaciones —
si automation_dispatcher.py no existe, el scheduler sigue funcionando.
"""
import logging
from datetime import datetime, timezone, timedelta

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# ── Deduplicación en memoria ──────────────────────────────────────────────────
# Evita disparar el mismo trigger dos veces en el mismo día para el mismo vuelo.
# Clave: (flight_id, hours_before, "YYYY-MM-DD") → fecha en que se despachó
_departing_soon_cache: dict[tuple, str] = {}


def _get_db():
    return SessionLocal()


def job_check_flight_departing_soon() -> None:
    """
    Detecta vuelos cuya salida programada cae en la ventana
    [now + hours_before - 30min, now + hours_before + 30min]
    para cada automatización activa con trigger_ref=flights_tracker.flight_departing_soon.

    Deduplicación: (flight_id, hours_before, "YYYY-MM-DD") — una vez por día.
    """
    db = _get_db()
    try:
        from app.modules.automations_engine.models.automation import Automation
        from .flight import Flight
        from .automation_handlers import _flight_to_dict

        now      = datetime.now(timezone.utc)
        today    = now.strftime("%Y-%m-%d")

        automations = db.query(Automation).filter(
            Automation.trigger_ref == "flights_tracker.flight_departing_soon",
            Automation.is_active   == True,
        ).all()

        # Agrupar por (user_id, hours_before) para minimizar queries
        processed: set[tuple] = set()  # (user_id, hours_before) ya procesados en esta ejecución

        for automation in automations:
            user_id = automation.user_id

            # Extraer hours_before de la config del nodo trigger
            flow         = automation.flow or {}
            nodes        = flow.get("nodes", [])
            trigger_node = next((n for n in nodes if n.get("type") == "trigger"), None)
            config       = trigger_node.get("config", {}) if trigger_node else {}
            hours_before = int(config.get("hours_before", 24))

            pair_key = (user_id, hours_before)
            if pair_key in processed:
                continue
            processed.add(pair_key)

            # Ventana: [now + hours_before - 30min, now + hours_before + 30min]
            window_start = now + timedelta(hours=hours_before) - timedelta(minutes=30)
            window_end   = now + timedelta(hours=hours_before) + timedelta(minutes=30)

            flights = db.query(Flight).filter(
                Flight.user_id            == user_id,
                Flight.is_past            == False,
                Flight.scheduled_departure >= window_start,
                Flight.scheduled_departure <= window_end,
            ).all()

            for flight in flights:
                dedup_key = (flight.id, hours_before, today)
                if _departing_soon_cache.get(dedup_key) == today:
                    continue  # ya despachado hoy para este (vuelo, umbral)

                hours_until = (flight.scheduled_departure - now).total_seconds() / 3600
                logger.info(
                    f"Vuelo próximo: '{flight.flight_number}' (id={flight.id}, "
                    f"user={user_id}, hours_until={hours_until:.1f}, threshold={hours_before}h)"
                )
                _departing_soon_cache[dedup_key] = today

                try:
                    from .automation_dispatcher import dispatcher
                    dispatcher.on_flight_departing_soon(
                        flight_id=flight.id,
                        hours_until_departure=hours_until,
                        flight_dict=_flight_to_dict(flight),
                        user_id=user_id,
                        db=db,
                    )
                except ImportError:
                    pass
                except Exception as e:
                    logger.warning(f"automation_dispatcher.on_flight_departing_soon falló: {e}")

    except Exception as e:
        logger.error(f"job_check_flight_departing_soon error: {e}")
    finally:
        db.close()
