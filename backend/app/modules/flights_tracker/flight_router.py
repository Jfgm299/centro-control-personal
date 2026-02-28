from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from .services import flight_service, passport_service
from .flight_schema import (
    FlightCreate,
    FlightResponse,
    FlightUpdate,
    FlightSearchResponse,
    PassportResponse,
)

router = APIRouter(prefix="/flights", tags=["Flights"])

# ── ORDEN CRÍTICO: rutas literales ANTES que rutas con parámetros ─────────────

@router.get("/search", response_model=FlightSearchResponse, description="⚡ Consume 1 llamada a AeroDataBox")
async def search_flight(
    flight_number: str,
    flight_date: date,
    user: User = Depends(get_current_user),
):
    return await flight_service.search_flight(flight_number, str(flight_date))


@router.get("/passport", response_model=PassportResponse)
def get_passport(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flights = flight_service.get_flights(db, user_id=user.id)
    return passport_service.calculate_passport(flights)


@router.post("/", response_model=FlightResponse, description="⚡ Consume 1 llamada a AeroDataBox", status_code=201)
async def add_flight(
    data: FlightCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await flight_service.add_flight(db, user_id=user.id, data=data)


@router.get("/", response_model=List[FlightResponse])
def get_flights(
    past: bool | None = None,
    upcoming: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return flight_service.get_flights(db, user_id=user.id, past=past, upcoming=upcoming, limit=limit, offset=offset)


# ── Rutas con parámetro SIEMPRE al final ─────────────────────────────────────

@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight(
    flight_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return flight_service.get_flight_by_id(db, user_id=user.id, flight_id=flight_id)


@router.patch("/{flight_id}/notes", response_model=FlightResponse)
def update_notes(
    flight_id: int,
    data: FlightUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return flight_service.update_notes(db, user_id=user.id, flight_id=flight_id, notes=data.notes)


@router.post("/{flight_id}/refresh", description="⚡ Consume 1 llamada a AeroDataBox",  response_model=FlightResponse)
async def refresh_flight(
    flight_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await flight_service.refresh_flight(db, user_id=user.id, flight_id=flight_id)


@router.delete("/{flight_id}", status_code=204)
def delete_flight(
    flight_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flight_service.delete_flight(db, user_id=user.id, flight_id=flight_id)
