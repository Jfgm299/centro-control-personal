from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from ..aerodatabox_client import AeroDataBoxClient
from ..exceptions import (
    FlightAlreadyExistsError,
    FlightNotFoundError,
    FlightRefreshThrottleError,
)
from ..flight import Flight
from ..flight_schema import FlightCreate


def _is_past(actual_arrival, scheduled_arrival) -> bool:
    now = datetime.now(timezone.utc)
    if actual_arrival and actual_arrival < now:
        return True
    if scheduled_arrival and scheduled_arrival < now - timedelta(hours=2):
        return True
    return False


class FlightService:

    async def add_flight(self, db: Session, user_id: int, data: FlightCreate) -> Flight:
        existing = db.query(Flight).filter(
            Flight.user_id       == user_id,
            Flight.flight_number == data.flight_number,
            Flight.flight_date   == data.flight_date,
        ).first()
        if existing:
            raise FlightAlreadyExistsError(data.flight_number, str(data.flight_date))

        client = AeroDataBoxClient()
        raw    = await client.get_flight(data.flight_number, str(data.flight_date))
        parsed = client.parse_flight_data(raw)

        flight = Flight(
            user_id           = user_id,
            flight_number     = data.flight_number,
            flight_date       = data.flight_date,
            notes             = data.notes,
            is_past           = _is_past(parsed.get("actual_arrival"), parsed.get("scheduled_arrival")),
            last_refreshed_at = datetime.now(timezone.utc),
            **parsed,
        )

        db.add(flight)
        db.commit()
        db.refresh(flight)
        return flight

    def get_flights(
        self,
        db: Session,
        user_id: int,
        past: bool | None = None,
        upcoming: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Flight]:
        query = db.query(Flight).filter(Flight.user_id == user_id)

        if past is True:
            query = query.filter(Flight.is_past == True).order_by(Flight.flight_date.desc())
        elif upcoming is True:
            query = query.filter(Flight.is_past == False).order_by(Flight.flight_date.asc())
        else:
            query = query.order_by(Flight.flight_date.desc())

        return query.limit(min(limit, 100)).offset(offset).all()

    def get_flight_by_id(self, db: Session, user_id: int, flight_id: int) -> Flight:
        flight = db.query(Flight).filter(
            Flight.id      == flight_id,
            Flight.user_id == user_id,
        ).first()
        if not flight:
            raise FlightNotFoundError(flight_id)
        return flight

    def delete_flight(self, db: Session, user_id: int, flight_id: int) -> None:
        flight = self.get_flight_by_id(db, user_id, flight_id)
        db.delete(flight)
        db.commit()

    async def refresh_flight(self, db: Session, user_id: int, flight_id: int) -> Flight:
        flight = self.get_flight_by_id(db, user_id, flight_id)

        if flight.last_refreshed_at:
            elapsed = datetime.now(timezone.utc) - flight.last_refreshed_at
            if elapsed < timedelta(minutes=5):
                raise FlightRefreshThrottleError()

        client = AeroDataBoxClient()
        raw    = await client.get_flight(flight.flight_number, str(flight.flight_date))
        parsed = client.parse_flight_data(raw)

        for key, value in parsed.items():
            setattr(flight, key, value)

        flight.is_past           = _is_past(parsed.get("actual_arrival"), parsed.get("scheduled_arrival"))
        flight.last_refreshed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(flight)
        return flight

    async def search_flight(self, flight_number: str, flight_date: str) -> dict:
        client = AeroDataBoxClient()
        raw    = await client.get_flight(flight_number, flight_date)
        parsed = client.parse_flight_data(raw)
        parsed["flight_number"] = flight_number
        return parsed

    def update_notes(self, db: Session, user_id: int, flight_id: int, notes: str | None) -> Flight:
        flight       = self.get_flight_by_id(db, user_id, flight_id)
        flight.notes = notes
        db.commit()
        db.refresh(flight)
        return flight


flight_service = FlightService()