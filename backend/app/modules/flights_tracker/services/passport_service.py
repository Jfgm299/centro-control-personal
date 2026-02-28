from collections import Counter
from datetime import date, timedelta
from typing import Optional

from ..flight import Flight
from ..flight_schema import (
    AircraftStat,
    AirlineStat,
    AirportStat,
    CountryVisit,
    DelayReport,
    FlightResponse,
    PassportResponse,
    YearStat,
)


class PassportService:

    def calculate_passport(self, flights: list[Flight]) -> PassportResponse:
        past   = [f for f in flights if f.is_past]
        future = [f for f in flights if not f.is_past]

        if not past:
            return self._empty_passport(future)

        return PassportResponse(
            # Totales
            total_flights         = len(past),
            total_distance_km     = self._total_distance(past),
            total_duration_hours  = self._total_duration_hours(past),
            avg_flight_distance_km    = self._avg_distance(past),
            avg_flight_duration_hours = self._avg_duration_hours(past),

            # Únicos
            unique_countries_count = len(self._unique_countries(past)),
            unique_airports_count  = len(self._unique_airports(past)),
            unique_airlines_count  = len(self._unique_airlines(past)),
            unique_aircraft_count  = len(self._unique_aircraft(past)),

            # Rankings
            countries_visited = self._countries_visited(past),
            airports_top      = self._airports_top(past),
            airlines_top      = self._airlines_top(past),
            aircraft_stats    = self._aircraft_stats(past),
            flights_by_year   = self._flights_by_year(past),

            # Highlights
            longest_flight     = self._longest_flight(past),
            shortest_flight    = self._shortest_flight(past),
            most_recent_flight = self._most_recent_flight(past),
            first_flight_date  = min(f.flight_date for f in past),

            # Próximo vuelo
            next_flight = self._next_flight(future),

            # Racha
            current_streak_days = self._streak(past),

            # Retrasos
            delay_report = self._delay_report(past),
        )

    # ── Helpers de totales ────────────────────────────────────────────────────

    def _total_distance(self, flights: list[Flight]) -> float:
        return round(sum(f.distance_km for f in flights if f.distance_km), 2)

    def _total_duration_hours(self, flights: list[Flight]) -> float:
        total = sum(f.duration_minutes for f in flights if f.duration_minutes)
        return round(total / 60, 2)

    def _avg_distance(self, flights: list[Flight]) -> Optional[float]:
        values = [f.distance_km for f in flights if f.distance_km]
        return round(sum(values) / len(values), 2) if values else None

    def _avg_duration_hours(self, flights: list[Flight]) -> Optional[float]:
        values = [f.duration_minutes for f in flights if f.duration_minutes]
        return round(sum(values) / len(values) / 60, 2) if values else None

    # ── Helpers de únicos ─────────────────────────────────────────────────────

    def _unique_countries(self, flights: list[Flight]) -> set:
        codes = set()
        for f in flights:
            if f.origin_country_code:
                codes.add(f.origin_country_code)
            if f.destination_country_code:
                codes.add(f.destination_country_code)
        return codes

    def _unique_airports(self, flights: list[Flight]) -> set:
        iatas = set()
        for f in flights:
            if f.origin_iata:
                iatas.add(f.origin_iata)
            if f.destination_iata:
                iatas.add(f.destination_iata)
        return iatas

    def _unique_airlines(self, flights: list[Flight]) -> set:
        return {f.airline_iata for f in flights if f.airline_iata}

    def _unique_aircraft(self, flights: list[Flight]) -> set:
        return {f.aircraft_model for f in flights if f.aircraft_model}

    # ── Rankings ──────────────────────────────────────────────────────────────

    def _countries_visited(self, flights: list[Flight]) -> list[CountryVisit]:
        # Acumular datos por país
        country_data: dict[str, dict] = {}
        for f in flights:
            for code, city, flight_date in [
                (f.origin_country_code,      f.origin_city,      f.flight_date),
                (f.destination_country_code, f.destination_city, f.flight_date),
            ]:
                if not code:
                    continue
                if code not in country_data:
                    country_data[code] = {
                        "visit_count": 0,
                        "cities": set(),
                        "first_visit": flight_date,
                    }
                country_data[code]["visit_count"] += 1
                if city:
                    country_data[code]["cities"].add(city)
                if flight_date < country_data[code]["first_visit"]:
                    country_data[code]["first_visit"] = flight_date

        return sorted(
            [
                CountryVisit(
                    country_code = code,
                    visit_count  = data["visit_count"],
                    cities       = sorted(data["cities"]),
                    first_visit  = data["first_visit"],
                )
                for code, data in country_data.items()
            ],
            key=lambda x: x.visit_count,
            reverse=True,
        )

    def _airports_top(self, flights: list[Flight], top: int = 10) -> list[AirportStat]:
        # Acumular info por IATA
        airport_info: dict[str, dict] = {}
        for f in flights:
            for iata, name, city, country in [
                (f.origin_iata,      f.origin_name,      f.origin_city,      f.origin_country_code),
                (f.destination_iata, f.destination_name, f.destination_city, f.destination_country_code),
            ]:
                if not iata:
                    continue
                if iata not in airport_info:
                    airport_info[iata] = {"name": name, "city": city, "country": country, "count": 0}
                airport_info[iata]["count"] += 1

        return sorted(
            [
                AirportStat(
                    iata         = iata,
                    name         = info["name"],
                    city         = info["city"],
                    country_code = info["country"],
                    flight_count = info["count"],
                )
                for iata, info in airport_info.items()
            ],
            key=lambda x: x.flight_count,
            reverse=True,
        )[:top]

    def _airlines_top(self, flights: list[Flight], top: int = 10) -> list[AirlineStat]:
        airline_info: dict[str, dict] = {}
        for f in flights:
            if not f.airline_iata:
                continue
            if f.airline_iata not in airline_info:
                airline_info[f.airline_iata] = {
                    "icao":   f.airline_icao,
                    "name":   f.airline_name,
                    "count":  0,
                    "delays": [],
                }
            airline_info[f.airline_iata]["count"] += 1
            if f.delay_arrival_minutes is not None:
                airline_info[f.airline_iata]["delays"].append(f.delay_arrival_minutes)

        result = []
        for iata, info in airline_info.items():
            delays = info["delays"]
            avg_delay = round(sum(delays) / len(delays), 1) if delays else None
            result.append(AirlineStat(
                iata               = iata,
                icao               = info["icao"],
                name               = info["name"],
                flight_count       = info["count"],
                avg_delay_minutes  = avg_delay,
            ))

        return sorted(result, key=lambda x: x.flight_count, reverse=True)[:top]

    def _aircraft_stats(self, flights: list[Flight], top: int = 10) -> list[AircraftStat]:
        aircraft_info: dict[str, dict] = {}
        for f in flights:
            if not f.aircraft_model:
                continue
            if f.aircraft_model not in aircraft_info:
                aircraft_info[f.aircraft_model] = {
                    "count":         0,
                    "registrations": set(),
                    "distance_km":   0.0,
                }
            aircraft_info[f.aircraft_model]["count"] += 1
            if f.aircraft_registration:
                aircraft_info[f.aircraft_model]["registrations"].add(f.aircraft_registration)
            if f.distance_km:
                aircraft_info[f.aircraft_model]["distance_km"] += f.distance_km

        return sorted(
            [
                AircraftStat(
                    model              = model,
                    flight_count       = info["count"],
                    registrations      = sorted(info["registrations"]),
                    total_distance_km  = round(info["distance_km"], 2),
                )
                for model, info in aircraft_info.items()
            ],
            key=lambda x: x.flight_count,
            reverse=True,
        )[:top]

    def _flights_by_year(self, flights: list[Flight]) -> list[YearStat]:
        year_data: dict[int, dict] = {}
        for f in flights:
            y = f.flight_date.year
            if y not in year_data:
                year_data[y] = {"count": 0, "distance": 0.0, "duration": 0, "delay": 0}
            year_data[y]["count"]    += 1
            year_data[y]["distance"] += f.distance_km or 0.0
            year_data[y]["duration"] += f.duration_minutes or 0
            year_data[y]["delay"]    += max(f.delay_arrival_minutes or 0, 0)

        return sorted(
            [
                YearStat(
                    year                 = year,
                    flight_count         = data["count"],
                    total_distance_km    = round(data["distance"], 2),
                    total_duration_hours = round(data["duration"] / 60, 2),
                    total_delay_hours    = round(data["delay"] / 60, 2),
                )
                for year, data in year_data.items()
            ],
            key=lambda x: x.year,
            reverse=True,
        )

    # ── Highlights ────────────────────────────────────────────────────────────

    def _longest_flight(self, flights: list[Flight]) -> Optional[FlightResponse]:
        candidates = [f for f in flights if f.distance_km]
        if not candidates:
            return None
        return FlightResponse.model_validate(max(candidates, key=lambda f: f.distance_km))

    def _shortest_flight(self, flights: list[Flight]) -> Optional[FlightResponse]:
        candidates = [f for f in flights if f.distance_km]
        if not candidates:
            return None
        return FlightResponse.model_validate(min(candidates, key=lambda f: f.distance_km))

    def _most_recent_flight(self, flights: list[Flight]) -> Optional[FlightResponse]:
        if not flights:
            return None
        return FlightResponse.model_validate(max(flights, key=lambda f: f.flight_date))

    def _next_flight(self, future: list[Flight]) -> Optional[FlightResponse]:
        if not future:
            return None
        return FlightResponse.model_validate(min(future, key=lambda f: f.flight_date))

    # ── Racha ─────────────────────────────────────────────────────────────────

    def _streak(self, flights: list[Flight]) -> int:
        flight_dates = {f.flight_date for f in flights}
        today = date.today()

        if today not in flight_dates and (today - timedelta(days=1)) not in flight_dates:
            return 0

        day = today if today in flight_dates else today - timedelta(days=1)
        streak = 0
        while day in flight_dates:
            streak += 1
            day -= timedelta(days=1)
        return streak

    # ── Delay report ──────────────────────────────────────────────────────────

    def _delay_report(self, flights: list[Flight]) -> DelayReport:
        total_delay_min = sum(max(f.delay_arrival_minutes or 0, 0) for f in flights)
        on_time         = [f for f in flights if (f.delay_arrival_minutes or 0) <= 15]
        delayed         = [f for f in flights if (f.delay_arrival_minutes or 0) > 15]
        worst           = max(flights, key=lambda f: f.delay_arrival_minutes or 0)

        return DelayReport(
            total_hours_lost     = round(total_delay_min / 60, 2),
            worst_delay_minutes  = worst.delay_arrival_minutes if worst.delay_arrival_minutes else None,
            worst_delay_flight   = FlightResponse.model_validate(worst) if worst.delay_arrival_minutes else None,
            on_time_percentage   = round(len(on_time) / len(flights) * 100, 1),
            pct_flights_delayed  = round(len(delayed) / len(flights) * 100, 1),
        )

    # ── Pasaporte vacío ───────────────────────────────────────────────────────

    def _empty_passport(self, future: list[Flight]) -> PassportResponse:
        return PassportResponse(
            total_flights             = 0,
            total_distance_km         = 0.0,
            total_duration_hours      = 0.0,
            avg_flight_distance_km    = None,
            avg_flight_duration_hours = None,
            unique_countries_count    = 0,
            unique_airports_count     = 0,
            unique_airlines_count     = 0,
            unique_aircraft_count     = 0,
            countries_visited         = [],
            airports_top              = [],
            airlines_top              = [],
            aircraft_stats            = [],
            flights_by_year           = [],
            longest_flight            = None,
            shortest_flight           = None,
            most_recent_flight        = None,
            first_flight_date         = None,
            next_flight               = self._next_flight(future),
            current_streak_days       = 0,
            delay_report              = DelayReport(
                total_hours_lost    = 0.0,
                worst_delay_minutes = None,
                worst_delay_flight  = None,
                on_time_percentage  = 100.0,
                pct_flights_delayed = 0.0,
            ),
        )


passport_service = PassportService()