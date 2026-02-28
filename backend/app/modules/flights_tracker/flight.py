import enum
from sqlalchemy import (
    Column, Integer, Float, String, Date, DateTime,
    Boolean, Text, Enum, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FlightStatus(str, enum.Enum):
    # Estados activos / en curso
    expected           = "expected"
    check_in           = "check_in"
    boarding           = "boarding"
    gate_closed        = "gate_closed"
    departed           = "departed"
    en_route           = "en_route"
    approaching        = "approaching"
    delayed            = "delayed"
    # Estados finales
    arrived            = "arrived"
    canceled           = "canceled"
    diverted           = "diverted"
    canceled_uncertain = "canceled_uncertain"
    unknown            = "unknown"


class Flight(Base):
    __tablename__ = "flights"
    __table_args__ = (
        UniqueConstraint("user_id", "flight_number", "flight_date"),
        Index("ix_flights_user_date", "user_id", "flight_date"),
        Index("ix_flights_user_past", "user_id", "is_past"),
        {"schema": "flights_tracker"},
    )

    # ── Identidad ─────────────────────────────────────────────────
    id            = Column(Integer, primary_key=True)
    user_id       = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    flight_number = Column(String(10), nullable=False)
    flight_date   = Column(Date, nullable=False)
    status        = Column(Enum(FlightStatus, schema="flights_tracker"), nullable=False, default=FlightStatus.unknown)

    # ── Aeropuerto origen ─────────────────────────────────────────
    origin_iata         = Column(String(4),   nullable=False)
    origin_icao         = Column(String(5),   nullable=True)
    origin_name         = Column(String(200), nullable=True)
    origin_city         = Column(String(100), nullable=True)
    origin_country_code = Column(String(3),   nullable=True)
    origin_timezone     = Column(String(50),  nullable=True)
    origin_lat          = Column(Float,        nullable=True)
    origin_lon          = Column(Float,        nullable=True)

    # ── Aeropuerto destino ────────────────────────────────────────
    destination_iata         = Column(String(4),   nullable=False)
    destination_icao         = Column(String(5),   nullable=True)
    destination_name         = Column(String(200), nullable=True)
    destination_city         = Column(String(100), nullable=True)
    destination_country_code = Column(String(3),   nullable=True)
    destination_timezone     = Column(String(50),  nullable=True)
    destination_lat          = Column(Float,        nullable=True)
    destination_lon          = Column(Float,        nullable=True)

    # ── Aerolínea ─────────────────────────────────────────────────
    airline_iata = Column(String(3),   nullable=True)
    airline_icao = Column(String(4),   nullable=True)
    airline_name = Column(String(100), nullable=True)

    # ── Tiempos de salida ─────────────────────────────────────────
    scheduled_departure  = Column(DateTime(timezone=True), nullable=True)
    revised_departure    = Column(DateTime(timezone=True), nullable=True)
    predicted_departure  = Column(DateTime(timezone=True), nullable=True)
    actual_departure     = Column(DateTime(timezone=True), nullable=True)

    # ── Tiempos de llegada ────────────────────────────────────────
    scheduled_arrival  = Column(DateTime(timezone=True), nullable=True)
    revised_arrival    = Column(DateTime(timezone=True), nullable=True)
    predicted_arrival  = Column(DateTime(timezone=True), nullable=True)
    actual_arrival     = Column(DateTime(timezone=True), nullable=True)

    # ── Métricas calculadas ───────────────────────────────────────
    duration_minutes         = Column(Integer, nullable=True)
    delay_departure_minutes  = Column(Integer, nullable=True)
    delay_arrival_minutes    = Column(Integer, nullable=True)
    distance_km              = Column(Float,   nullable=True)

    # ── Avión ─────────────────────────────────────────────────────
    aircraft_model        = Column(String(100), nullable=True)
    aircraft_registration = Column(String(20),  nullable=True)
    aircraft_icao24       = Column(String(10),  nullable=True)

    # ── Detalles operacionales ────────────────────────────────────
    terminal_origin      = Column(String(10), nullable=True)
    gate_origin          = Column(String(10), nullable=True)
    terminal_destination = Column(String(10), nullable=True)
    baggage_belt         = Column(String(10), nullable=True)
    runway_origin        = Column(String(10), nullable=True)
    runway_destination   = Column(String(10), nullable=True)
    data_quality         = Column(String(50), nullable=True)

    # ── Flags ─────────────────────────────────────────────────────
    is_past     = Column(Boolean, nullable=False, default=False)
    is_diverted = Column(Boolean, nullable=False, default=False)

    # ── Usuario ───────────────────────────────────────────────────
    notes = Column(Text, nullable=True)

    # ── Control ───────────────────────────────────────────────────
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relaciones ────────────────────────────────────────────────
    user = relationship("User", back_populates="flights")