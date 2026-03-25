"""
Handlers de automatizaciones para flights_tracker.
Contrato: handler(payload, config, db, user_id) -> dict

TRIGGERS:
    handle_flight_added            — Vuelo registrado
    handle_flight_status_changed   — Estado del vuelo cambió
    handle_flight_departing_soon   — Vuelo sale en N horas

ACCIONES:
    action_get_flight_details      — Obtener info completa del vuelo
    action_refresh_flight          — Refrescar datos via AeroDataBox
"""
from sqlalchemy.orm import Session

from .flight import Flight


# ── Utilidades internas ───────────────────────────────────────────────────────

def _flight_to_dict(flight: Flight) -> dict:
    return {
        "id":                       flight.id,
        "flight_number":            flight.flight_number,
        "flight_date":              str(flight.flight_date) if flight.flight_date else None,
        "status":                   flight.status.value if flight.status else None,
        "origin_iata":              flight.origin_iata,
        "destination_iata":         flight.destination_iata,
        "airline_name":             flight.airline_name,
        "scheduled_departure":      flight.scheduled_departure.isoformat() if flight.scheduled_departure else None,
        "actual_departure":         flight.actual_departure.isoformat() if flight.actual_departure else None,
        "scheduled_arrival":        flight.scheduled_arrival.isoformat() if flight.scheduled_arrival else None,
        "actual_arrival":           flight.actual_arrival.isoformat() if flight.actual_arrival else None,
        "delay_departure_minutes":  flight.delay_departure_minutes,
        "delay_arrival_minutes":    flight.delay_arrival_minutes,
        "is_past":                  flight.is_past,
        "is_diverted":              flight.is_diverted,
    }


# ── TRIGGER HANDLERS ──────────────────────────────────────────────────────────

def handle_flight_added(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando se registra un vuelo.
    Payload esperado: {"flight_id": int, "flight_number": str, "flight_date": str, "status": str}
    Config: ninguna
    """
    flight_id = payload.get("flight_id")
    if not flight_id:
        return {"matched": False, "reason": "no flight_id in payload"}

    flight = db.query(Flight).filter(
        Flight.id      == flight_id,
        Flight.user_id == user_id,
    ).first()

    if not flight:
        return {"matched": False, "reason": f"flight {flight_id} not found"}

    return {"matched": True, "flight": _flight_to_dict(flight)}


def handle_flight_status_changed(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando el estado de un vuelo cambia.
    Payload esperado: {"flight_id": int, "old_status": str, "new_status": str, "flight": dict}
    Config:
        - to_status: str  — filtrar por estado destino (opcional)
    """
    flight_id  = payload.get("flight_id")
    new_status = payload.get("new_status")

    if not flight_id:
        return {"matched": False, "reason": "no flight_id in payload"}

    to_status = config.get("to_status")
    if to_status and new_status != to_status:
        return {
            "matched": False,
            "reason":  f"new_status '{new_status}' does not match filter '{to_status}'",
        }

    flight = db.query(Flight).filter(
        Flight.id      == flight_id,
        Flight.user_id == user_id,
    ).first()

    if not flight:
        return {"matched": False, "reason": f"flight {flight_id} not found"}

    return {
        "matched":    True,
        "flight":     _flight_to_dict(flight),
        "old_status": payload.get("old_status"),
        "new_status": new_status,
    }


def handle_flight_departing_soon(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: cuando un vuelo sale en N horas.
    Payload esperado: {"flight_id": int, "hours_until_departure": float, "flight": dict}
    Config:
        - hours_before: int  — umbral en horas (default 24)
    """
    flight_id             = payload.get("flight_id")
    hours_until_departure = payload.get("hours_until_departure", 0)

    if not flight_id:
        return {"matched": False, "reason": "no flight_id in payload"}

    hours_before = config.get("hours_before", 24)

    # El scheduler ya verificó la ventana; validamos por si acaso
    if hours_until_departure > hours_before + 0.5:
        return {
            "matched": False,
            "reason":  f"hours_until_departure {hours_until_departure:.1f} > threshold {hours_before}",
        }

    flight = db.query(Flight).filter(
        Flight.id      == flight_id,
        Flight.user_id == user_id,
    ).first()

    if not flight:
        return {"matched": False, "reason": f"flight {flight_id} not found"}

    return {
        "matched":              True,
        "flight":               _flight_to_dict(flight),
        "hours_until_departure": hours_until_departure,
        "hours_before":          hours_before,
    }


# ── ACTION HANDLERS ───────────────────────────────────────────────────────────

def action_get_flight_details(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: obtener detalles completos de un vuelo.
    Config:
        - flight_id: int  — ID del vuelo (opcional, fallback a payload)
    """
    flight_id = config.get("flight_id") or payload.get("flight_id")
    if not flight_id:
        return {"done": False, "reason": "no flight_id in config or payload"}

    flight = db.query(Flight).filter(
        Flight.id      == flight_id,
        Flight.user_id == user_id,
    ).first()

    if not flight:
        return {"done": False, "reason": f"flight {flight_id} not found"}

    flight_dict = _flight_to_dict(flight)
    fields = config.get("fields") or []
    if fields:
        flight_dict = {k: v for k, v in flight_dict.items() if k in fields}

    return {"done": True, "flight": flight_dict}


def action_refresh_flight(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: actualizar datos del vuelo via AeroDataBox API.
    Config:
        - flight_id: int  — ID del vuelo (opcional, fallback a payload)

    NOTA: flight_service.refresh_flight() es async. Se ejecuta sincrónicamente
    creando un event loop nuevo para evitar conflictos con el loop de FastAPI.
    """
    import asyncio
    from .services.flight_service import flight_service
    from .exceptions import FlightRefreshThrottleError, FlightNotFoundError

    flight_id = config.get("flight_id") or payload.get("flight_id")
    if not flight_id:
        return {"done": False, "reason": "no flight_id in config or payload"}

    try:
        loop = asyncio.new_event_loop()
        try:
            flight = loop.run_until_complete(
                flight_service.refresh_flight(db, user_id, flight_id)
            )
        finally:
            loop.close()

        return {"done": True, "flight": _flight_to_dict(flight)}

    except FlightRefreshThrottleError:
        return {"done": False, "reason": "throttled"}
    except FlightNotFoundError:
        return {"done": False, "reason": f"flight {flight_id} not found"}
    except Exception as e:
        return {"done": False, "reason": str(e)}
