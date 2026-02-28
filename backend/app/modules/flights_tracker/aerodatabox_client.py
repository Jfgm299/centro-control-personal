import math
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings
from .exceptions import (
    FlightNotFoundInAPIError,
    AeroDataBoxTimeoutError,
    AeroDataBoxRateLimitError,
    AeroDataBoxError,
)
from .flight import FlightStatus


STATUS_MAP = {
    "Unknown":           FlightStatus.unknown,
    "Expected":          FlightStatus.expected,
    "EnRoute":           FlightStatus.en_route,
    "CheckIn":           FlightStatus.check_in,
    "Boarding":          FlightStatus.boarding,
    "GateClosed":        FlightStatus.gate_closed,
    "Departed":          FlightStatus.departed,
    "Delayed":           FlightStatus.delayed,
    "Approaching":       FlightStatus.approaching,
    "Arrived":           FlightStatus.arrived,
    "Canceled":          FlightStatus.canceled,
    "Diverted":          FlightStatus.diverted,
    "CanceledUncertain": FlightStatus.canceled_uncertain,
}


class AeroDataBoxClient:
    BASE_URL = settings.AERODATABOX_BASE_URL
    HEADERS = {
        "X-RapidAPI-Key":  settings.AERODATABOX_API_KEY,
        "X-RapidAPI-Host": settings.AERODATABOX_HOST,
    }
    TIMEOUT = 10.0

    async def get_flight(self, flight_number: str, date: str) -> dict:
        """GET /flights/number/{flight_number}/{date}?dateLocalRole=Both"""
        url = f"{self.BASE_URL}/flights/number/{flight_number}/{date}"
        params = {"dateLocalRole": "Both"}
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, headers=self.HEADERS, params=params)

                if response.status_code == 204:
                    raise FlightNotFoundInAPIError(flight_number, date)
                if response.status_code == 404:
                    raise FlightNotFoundInAPIError(flight_number, date)
                if response.status_code == 429:
                    raise AeroDataBoxRateLimitError()
                if response.status_code >= 500:
                    raise AeroDataBoxError()

                response.raise_for_status()

                data = response.json()
                flights = data if isinstance(data, list) else [data]
                if not flights:
                    raise FlightNotFoundInAPIError(flight_number, date)

                return flights[0]

        except httpx.TimeoutException:
            raise AeroDataBoxTimeoutError()
        except (FlightNotFoundInAPIError, AeroDataBoxRateLimitError,
                AeroDataBoxError, AeroDataBoxTimeoutError):
            raise
        except httpx.HTTPError:
            raise AeroDataBoxError()

    def parse_flight_data(self, raw: dict) -> dict:
        """Extrae y normaliza todos los campos del contrato AeroDataBox."""
        dep    = raw.get("departure", {})
        arr    = raw.get("arrival",   {})
        dep_ap = dep.get("airport",   {})
        arr_ap = arr.get("airport",   {})
        dep_loc = dep_ap.get("location", {})
        arr_loc = arr_ap.get("location", {})
        airline  = raw.get("airline",  {})
        aircraft = raw.get("aircraft", {})
        dist     = raw.get("greatCircleDistance")

        # ── Tiempos ───────────────────────────────────────────────
        scheduled_departure  = self._parse_datetime(dep.get("scheduledTime",  {}).get("local"))
        revised_departure    = self._parse_datetime(dep.get("revisedTime",    {}).get("local"))
        predicted_departure  = self._parse_datetime(dep.get("predictedTime",  {}).get("local"))
        actual_departure     = self._parse_datetime(dep.get("runwayTime",     {}).get("local"))

        scheduled_arrival    = self._parse_datetime(arr.get("scheduledTime",  {}).get("local"))
        revised_arrival      = self._parse_datetime(arr.get("revisedTime",    {}).get("local"))
        predicted_arrival    = self._parse_datetime(arr.get("predictedTime",  {}).get("local"))
        actual_arrival       = self._parse_datetime(arr.get("runwayTime",     {}).get("local"))

        # ── Distancia ─────────────────────────────────────────────
        distance_km = None
        if dist and dist.get("km"):
            distance_km = float(dist["km"])
        elif dep_loc.get("lat") and arr_loc.get("lat"):
            distance_km = self._haversine_km(
                dep_loc["lat"], dep_loc["lon"],
                arr_loc["lat"], arr_loc["lon"],
            )

        # ── Métricas calculadas ───────────────────────────────────
        duration_minutes        = self._calculate_duration(actual_departure, actual_arrival,
                                                           scheduled_departure, scheduled_arrival)
        delay_departure_minutes = self._calculate_delay(scheduled_departure, actual_departure)
        delay_arrival_minutes   = self._calculate_delay(scheduled_arrival,   actual_arrival)

        # ── Status ────────────────────────────────────────────────
        adb_status = raw.get("status", "Unknown")
        status = STATUS_MAP.get(adb_status, FlightStatus.unknown)

        return {
            # Origen
            "origin_iata":         dep_ap.get("iata"),
            "origin_icao":         dep_ap.get("icao"),
            "origin_name":         dep_ap.get("name"),
            "origin_city":         dep_ap.get("municipalityName"),
            "origin_country_code": dep_ap.get("countryCode"),
            "origin_timezone":     dep_ap.get("timeZone"),
            "origin_lat":          dep_loc.get("lat"),
            "origin_lon":          dep_loc.get("lon"),
            # Destino
            "destination_iata":         arr_ap.get("iata"),
            "destination_icao":         arr_ap.get("icao"),
            "destination_name":         arr_ap.get("name"),
            "destination_city":         arr_ap.get("municipalityName"),
            "destination_country_code": arr_ap.get("countryCode"),
            "destination_timezone":     arr_ap.get("timeZone"),
            "destination_lat":          arr_loc.get("lat"),
            "destination_lon":          arr_loc.get("lon"),
            # Aerolínea
            "airline_iata": airline.get("iata"),
            "airline_icao": airline.get("icao"),
            "airline_name": airline.get("name"),
            # Tiempos salida
            "scheduled_departure": scheduled_departure,
            "revised_departure":   revised_departure,
            "predicted_departure": predicted_departure,
            "actual_departure":    actual_departure,
            # Tiempos llegada
            "scheduled_arrival": scheduled_arrival,
            "revised_arrival":   revised_arrival,
            "predicted_arrival": predicted_arrival,
            "actual_arrival":    actual_arrival,
            # Métricas
            "duration_minutes":        duration_minutes,
            "delay_departure_minutes": delay_departure_minutes,
            "delay_arrival_minutes":   delay_arrival_minutes,
            "distance_km":             distance_km,
            # Avión
            "aircraft_model":        aircraft.get("model"),
            "aircraft_registration": aircraft.get("reg"),
            "aircraft_icao24":       aircraft.get("modeS"),
            # Operacional
            "terminal_origin":      dep.get("terminal"),
            "gate_origin":          dep.get("gate"),
            "terminal_destination": arr.get("terminal"),
            "baggage_belt":         arr.get("baggageBelt"),
            "runway_origin":        dep.get("runway"),
            "runway_destination":   arr.get("runway"),
            "data_quality":         ",".join(dep.get("quality", [])),
            # Status y flags
            "status":       status,
            "is_diverted":  status == FlightStatus.diverted,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        """Parsea '2026-03-15 07:00+01:00' a datetime con timezone."""
        if not dt_str:
            return None
        try:
            # AeroDataBox devuelve formato "2026-03-15 07:00+01:00"
            return datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None

    def _calculate_duration(
        self,
        actual_dep: datetime | None,
        actual_arr: datetime | None,
        sched_dep:  datetime | None,
        sched_arr:  datetime | None,
    ) -> int | None:
        """Calcula duración en minutos. Usa tiempos reales si existen, si no programados."""
        dep = actual_dep or sched_dep
        arr = actual_arr or sched_arr
        if not dep or not arr:
            return None
        delta = arr - dep
        minutes = int(delta.total_seconds() / 60)
        return minutes if minutes > 0 else None

    def _calculate_delay(
        self,
        scheduled: datetime | None,
        actual:    datetime | None,
    ) -> int | None:
        """Calcula retraso en minutos. Negativo = adelantado."""
        if not scheduled or not actual:
            return None
        delta = actual - scheduled
        return int(delta.total_seconds() / 60)

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Distancia ortodrómica entre dos puntos GPS. Solo math stdlib."""
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi  = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))