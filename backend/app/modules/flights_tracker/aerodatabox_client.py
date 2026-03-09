import logging
import math
import httpx
from datetime import datetime

from .exceptions import (
    FlightNotFoundInAPIError,
    AeroDataBoxTimeoutError,
    AeroDataBoxRateLimitError,
    AeroDataBoxError,
)
from .flight import FlightStatus

logger = logging.getLogger(__name__)

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
    TIMEOUT = 10.0

    def __init__(self):
        import os
        from app.modules.flights_tracker.manifest import get_settings
        s = get_settings()
        api_key = s["AERODATABOX_API_KEY"]
        os_key = os.environ.get("AERODATABOX_API_KEY", "NOT_FOUND")
        os_preview = f"{os_key[:4]}...{os_key[-4:]}" if len(os_key) >= 8 else os_key
        key_preview = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else f"(len={len(api_key)})"
        logger.warning("AeroDataBoxClient init — settings key: %s | os.environ key: %s", key_preview, os_preview)
        self.BASE_URL = s["AERODATABOX_BASE_URL"]
        self.HEADERS = {
            "X-RapidAPI-Key":  api_key,
            "X-RapidAPI-Host": s["AERODATABOX_HOST"],
        }

    async def get_flight(self, flight_number: str, date: str) -> dict:
        """GET /flights/number/{flight_number}/{date}?dateLocalRole=Both"""
        url = f"{self.BASE_URL}/flights/number/{flight_number}/{date}"
        params = {"dateLocalRole": "Both"}
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, headers=self.HEADERS, params=params)

                logger.info("AeroDataBox response: %s %s", response.status_code, url)
                if response.status_code == 204:
                    raise FlightNotFoundInAPIError(flight_number, date)
                if response.status_code == 404:
                    raise FlightNotFoundInAPIError(flight_number, date)
                if response.status_code == 429:
                    raise AeroDataBoxRateLimitError()
                if response.status_code >= 500:
                    logger.error("AeroDataBox server error: %s body=%s", response.status_code, response.text[:200])
                    raise AeroDataBoxError()
                if response.status_code >= 400:
                    logger.error("AeroDataBox client error: %s body=%s", response.status_code, response.text[:200])
                    response.raise_for_status()

                response.raise_for_status()

                data = response.json()
                flights = data if isinstance(data, list) else [data]
                if not flights:
                    raise FlightNotFoundInAPIError(flight_number, date)

                return flights[0]

        except httpx.TimeoutException as e:
            logger.error("AeroDataBox timeout: %s", e)
            raise AeroDataBoxTimeoutError()
        except (FlightNotFoundInAPIError, AeroDataBoxRateLimitError,
                AeroDataBoxError, AeroDataBoxTimeoutError):
            raise
        except httpx.HTTPError as e:
            logger.error("AeroDataBox HTTP error: %s", e)
            raise AeroDataBoxError()

    def parse_flight_data(self, raw: dict) -> dict:
        """Extrae y normaliza todos los campos del contrato AeroDataBox."""
        dep     = raw.get("departure", {})
        arr     = raw.get("arrival",   {})
        dep_ap  = dep.get("airport",   {})
        arr_ap  = arr.get("airport",   {})
        dep_loc = dep_ap.get("location", {})
        arr_loc = arr_ap.get("location", {})
        airline  = raw.get("airline",  {})
        aircraft = raw.get("aircraft", {})
        dist     = raw.get("greatCircleDistance")

        scheduled_departure = self._parse_datetime(dep.get("scheduledTime", {}).get("local"))
        revised_departure   = self._parse_datetime(dep.get("revisedTime",   {}).get("local"))
        predicted_departure = self._parse_datetime(dep.get("predictedTime", {}).get("local"))
        actual_departure    = self._parse_datetime(dep.get("runwayTime",    {}).get("local"))

        scheduled_arrival   = self._parse_datetime(arr.get("scheduledTime", {}).get("local"))
        revised_arrival     = self._parse_datetime(arr.get("revisedTime",   {}).get("local"))
        predicted_arrival   = self._parse_datetime(arr.get("predictedTime", {}).get("local"))
        actual_arrival      = self._parse_datetime(arr.get("runwayTime",    {}).get("local"))

        distance_km = None
        if dist and dist.get("km"):
            distance_km = float(dist["km"])
        elif dep_loc.get("lat") and arr_loc.get("lat"):
            distance_km = self._haversine_km(
                dep_loc["lat"], dep_loc["lon"],
                arr_loc["lat"], arr_loc["lon"],
            )

        duration_minutes        = self._calculate_duration(actual_departure, actual_arrival,
                                                           scheduled_departure, scheduled_arrival)
        delay_departure_minutes = self._calculate_delay(scheduled_departure, actual_departure)
        delay_arrival_minutes   = self._calculate_delay(scheduled_arrival,   actual_arrival)

        adb_status = raw.get("status", "Unknown")
        status = STATUS_MAP.get(adb_status, FlightStatus.unknown)

        return {
            "origin_iata":         dep_ap.get("iata"),
            "origin_icao":         dep_ap.get("icao"),
            "origin_name":         dep_ap.get("name"),
            "origin_city":         dep_ap.get("municipalityName"),
            "origin_country_code": dep_ap.get("countryCode"),
            "origin_timezone":     dep_ap.get("timeZone"),
            "origin_lat":          dep_loc.get("lat"),
            "origin_lon":          dep_loc.get("lon"),
            "destination_iata":         arr_ap.get("iata"),
            "destination_icao":         arr_ap.get("icao"),
            "destination_name":         arr_ap.get("name"),
            "destination_city":         arr_ap.get("municipalityName"),
            "destination_country_code": arr_ap.get("countryCode"),
            "destination_timezone":     arr_ap.get("timeZone"),
            "destination_lat":          arr_loc.get("lat"),
            "destination_lon":          arr_loc.get("lon"),
            "airline_iata": airline.get("iata"),
            "airline_icao": airline.get("icao"),
            "airline_name": airline.get("name"),
            "scheduled_departure": scheduled_departure,
            "revised_departure":   revised_departure,
            "predicted_departure": predicted_departure,
            "actual_departure":    actual_departure,
            "scheduled_arrival":   scheduled_arrival,
            "revised_arrival":     revised_arrival,
            "predicted_arrival":   predicted_arrival,
            "actual_arrival":      actual_arrival,
            "duration_minutes":        duration_minutes,
            "delay_departure_minutes": delay_departure_minutes,
            "delay_arrival_minutes":   delay_arrival_minutes,
            "distance_km":             distance_km,
            "aircraft_model":        aircraft.get("model"),
            "aircraft_registration": aircraft.get("reg"),
            "aircraft_icao24":       aircraft.get("modeS"),
            "terminal_origin":      dep.get("terminal"),
            "gate_origin":          dep.get("gate"),
            "terminal_destination": arr.get("terminal"),
            "baggage_belt":         arr.get("baggageBelt"),
            "runway_origin":        dep.get("runway"),
            "runway_destination":   arr.get("runway"),
            "data_quality":         ",".join(dep.get("quality", [])),
            "status":      status,
            "is_diverted": status == FlightStatus.diverted,
        }

    def _parse_datetime(self, dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None

    def _calculate_duration(self, actual_dep, actual_arr, sched_dep, sched_arr) -> int | None:
        dep = actual_dep or sched_dep
        arr = actual_arr or sched_arr
        if not dep or not arr:
            return None
        minutes = int((arr - dep).total_seconds() / 60)
        return minutes if minutes > 0 else None

    def _calculate_delay(self, scheduled, actual) -> int | None:
        if not scheduled or not actual:
            return None
        return int((actual - scheduled).total_seconds() / 60)

    def _haversine_km(self, lat1, lon1, lat2, lon2) -> float:
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi    = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))