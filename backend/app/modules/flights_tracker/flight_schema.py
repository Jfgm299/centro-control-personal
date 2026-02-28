from datetime import date, datetime, timedelta
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from .flight import FlightStatus


# ── Input ─────────────────────────────────────────────────────────────────────

class FlightCreate(BaseModel):
    flight_number: str
    flight_date: date
    notes: Optional[str] = None

    @field_validator("flight_number")
    @classmethod
    def normalize_flight_number(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("flight_date")
    @classmethod
    def validate_date_range(cls, v: date) -> date:
        today = date.today()
        min_date = today - timedelta(days=365)
        max_date = today + timedelta(days=365)
        if not (min_date <= v <= max_date):
            raise ValueError("La fecha debe estar dentro del rango de ±1 año desde hoy")
        return v


class FlightUpdate(BaseModel):
    notes: Optional[str] = None
    @field_validator("notes")
    @classmethod
    def validate_notes_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("Las notas no pueden superar los 500 caracteres")
        return v


# ── Output ────────────────────────────────────────────────────────────────────

class FlightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    flight_number: str
    flight_date: date
    status: FlightStatus

    # Origen
    origin_iata: str
    origin_icao: Optional[str] = None
    origin_name: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country_code: Optional[str] = None
    origin_timezone: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None

    # Destino
    destination_iata: str
    destination_icao: Optional[str] = None
    destination_name: Optional[str] = None
    destination_city: Optional[str] = None
    destination_country_code: Optional[str] = None
    destination_timezone: Optional[str] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None

    # Aerolínea
    airline_iata: Optional[str] = None
    airline_icao: Optional[str] = None
    airline_name: Optional[str] = None

    # Tiempos salida
    scheduled_departure: Optional[datetime] = None
    revised_departure: Optional[datetime] = None
    predicted_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None

    # Tiempos llegada
    scheduled_arrival: Optional[datetime] = None
    revised_arrival: Optional[datetime] = None
    predicted_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None

    # Métricas
    duration_minutes: Optional[int] = None
    delay_departure_minutes: Optional[int] = None
    delay_arrival_minutes: Optional[int] = None
    distance_km: Optional[float] = None

    # Avión
    aircraft_model: Optional[str] = None
    aircraft_registration: Optional[str] = None
    aircraft_icao24: Optional[str] = None

    # Operacional
    terminal_origin: Optional[str] = None
    gate_origin: Optional[str] = None
    terminal_destination: Optional[str] = None
    baggage_belt: Optional[str] = None
    runway_origin: Optional[str] = None
    runway_destination: Optional[str] = None
    data_quality: Optional[str] = None

    # Flags
    is_past: bool
    is_diverted: bool

    # Usuario
    notes: Optional[str] = None

    # Control
    last_refreshed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FlightSearchResponse(BaseModel):
    """Resultado de búsqueda sin guardar — no tiene id ni campos de usuario."""
    flight_number: str
    flight_date: Optional[date] = None
    status: FlightStatus

    origin_iata: Optional[str] = None
    origin_icao: Optional[str] = None
    origin_name: Optional[str] = None
    origin_city: Optional[str] = None
    origin_country_code: Optional[str] = None
    origin_timezone: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lon: Optional[float] = None

    destination_iata: Optional[str] = None
    destination_icao: Optional[str] = None
    destination_name: Optional[str] = None
    destination_city: Optional[str] = None
    destination_country_code: Optional[str] = None
    destination_timezone: Optional[str] = None
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None

    airline_iata: Optional[str] = None
    airline_icao: Optional[str] = None
    airline_name: Optional[str] = None

    scheduled_departure: Optional[datetime] = None
    revised_departure: Optional[datetime] = None
    predicted_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None

    scheduled_arrival: Optional[datetime] = None
    revised_arrival: Optional[datetime] = None
    predicted_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None

    duration_minutes: Optional[int] = None
    delay_departure_minutes: Optional[int] = None
    delay_arrival_minutes: Optional[int] = None
    distance_km: Optional[float] = None

    aircraft_model: Optional[str] = None
    aircraft_registration: Optional[str] = None
    aircraft_icao24: Optional[str] = None

    terminal_origin: Optional[str] = None
    gate_origin: Optional[str] = None
    terminal_destination: Optional[str] = None
    baggage_belt: Optional[str] = None
    runway_origin: Optional[str] = None
    runway_destination: Optional[str] = None
    data_quality: Optional[str] = None


# ── Passport schemas ──────────────────────────────────────────────────────────

class CountryVisit(BaseModel):
    country_code: str
    country_name: Optional[str] = None
    visit_count: int
    cities: list[str]
    first_visit: Optional[date] = None


class AirportStat(BaseModel):
    iata: str
    name: Optional[str] = None
    city: Optional[str] = None
    country_code: Optional[str] = None
    flight_count: int


class AirlineStat(BaseModel):
    iata: Optional[str] = None
    icao: Optional[str] = None
    name: Optional[str] = None
    flight_count: int
    avg_delay_minutes: Optional[float] = None


class AircraftStat(BaseModel):
    model: str
    flight_count: int
    registrations: list[str]
    total_distance_km: float


class YearStat(BaseModel):
    year: int
    flight_count: int
    total_distance_km: float
    total_duration_hours: float
    total_delay_hours: float


class DelayReport(BaseModel):
    total_hours_lost: float
    worst_delay_minutes: Optional[int] = None
    worst_delay_flight: Optional[FlightResponse] = None
    on_time_percentage: float
    pct_flights_delayed: float


class PassportResponse(BaseModel):
    # Totales
    total_flights: int
    total_distance_km: float
    total_duration_hours: float
    avg_flight_distance_km: Optional[float] = None
    avg_flight_duration_hours: Optional[float] = None

    # Únicos
    unique_countries_count: int
    unique_airports_count: int
    unique_airlines_count: int
    unique_aircraft_count: int

    # Rankings
    countries_visited: list[CountryVisit]
    airports_top: list[AirportStat]
    airlines_top: list[AirlineStat]
    aircraft_stats: list[AircraftStat]
    flights_by_year: list[YearStat]

    # Highlights
    longest_flight: Optional[FlightResponse] = None
    shortest_flight: Optional[FlightResponse] = None
    most_recent_flight: Optional[FlightResponse] = None
    first_flight_date: Optional[date] = None

    # Próximo vuelo
    next_flight: Optional[FlightResponse] = None

    # Racha
    current_streak_days: int

    # Retrasos
    delay_report: DelayReport