import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date
import httpx

from app.modules.flights_tracker.aerodatabox_client import AeroDataBoxClient
from app.modules.flights_tracker.exceptions import (
    FlightNotFoundInAPIError,
    AeroDataBoxTimeoutError,
    AeroDataBoxRateLimitError,
)


MOCK_FLIGHT_RAW = {
    "number": "VY1234",
    "status": "Arrived",
    "greatCircleDistance": {
        "km": 621.5, "mile": 386.2, "nm": 335.6, "meter": 621500, "feet": 2038700
    },
    "departure": {
        "airport": {
            "iata": "MAD", "icao": "LEMD", "name": "Madrid Barajas",
            "municipalityName": "Madrid", "countryCode": "ES",
            "timeZone": "Europe/Madrid",
            "location": {"lat": 40.4719, "lon": -3.5626}
        },
        "scheduledTime": {"local": "2025-06-15 10:00+02:00", "utc": "2025-06-15 08:00Z"},
        "runwayTime": {"local": "2025-06-15 10:18+02:00"},
        "terminal": "T4", "gate": "B22",
        "quality": ["Basic", "Live"]
    },
    "arrival": {
        "airport": {
            "iata": "BCN", "icao": "LEBL", "name": "Barcelona El Prat",
            "municipalityName": "Barcelona", "countryCode": "ES",
            "timeZone": "Europe/Madrid",
            "location": {"lat": 41.2971, "lon": 2.0785}
        },
        "scheduledTime": {"local": "2025-06-15 11:15+02:00"},
        "runwayTime": {"local": "2025-06-15 11:22+02:00"},
        "terminal": "T1", "baggageBelt": "5",
        "quality": ["Basic", "Live"]
    },
    "airline": {"iata": "VY", "icao": "VLG", "name": "Vueling"},
    "aircraft": {"model": "Airbus A320", "reg": "EC-MGY", "modeS": "3443C2"},
    "lastUpdatedUtc": "2025-06-15T09:30:00Z",
    "codeshareStatus": "IsOperator",
    "isCargo": False
}

MOCK_PARTIAL_RAW = {
    "number": "IB3456",
    "status": "Unknown",
    "departure": {
        "airport": {"iata": "MAD", "icao": "LEMD", "name": "Madrid Barajas"},
        "quality": []
    },
    "arrival": {
        "airport": {"iata": "LHR", "icao": "EGLL", "name": "London Heathrow"},
        "quality": []
    },
    "codeshareStatus": "None",
    "isCargo": False,
    "lastUpdatedUtc": "2025-06-15T09:30:00Z"
}


class TestAeroDataBoxClient:

    @pytest.fixture
    def client(self):
        return AeroDataBoxClient()

    @pytest.mark.asyncio
    async def test_get_flight_success(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [MOCK_FLIGHT_RAW]

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            result = await client.get_flight("VY1234", "2025-06-15")

        assert result["number"] == "VY1234"

    @pytest.mark.asyncio
    async def test_get_flight_204_raises_not_found(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 204

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            with pytest.raises(FlightNotFoundInAPIError):
                await client.get_flight("XX9999", "2025-06-15")

    @pytest.mark.asyncio
    async def test_get_flight_404_raises_not_found(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            with pytest.raises(FlightNotFoundInAPIError):
                await client.get_flight("XX9999", "2025-06-15")

    @pytest.mark.asyncio
    async def test_get_flight_timeout_raises_timeout_error(self, client):
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            with pytest.raises(AeroDataBoxTimeoutError):
                await client.get_flight("VY1234", "2025-06-15")

    def test_parse_flight_data_complete_fields(self, client):
        result = client.parse_flight_data(MOCK_FLIGHT_RAW)

        assert result["origin_iata"] == "MAD"
        assert result["origin_icao"] == "LEMD"
        assert result["origin_name"] == "Madrid Barajas"
        assert result["origin_city"] == "Madrid"
        assert result["origin_country_code"] == "ES"
        assert result["destination_iata"] == "BCN"
        assert result["destination_name"] == "Barcelona El Prat"
        assert result["airline_iata"] == "VY"
        assert result["airline_name"] == "Vueling"
        assert result["aircraft_model"] == "Airbus A320"
        assert result["aircraft_registration"] == "EC-MGY"
        assert result["terminal_origin"] == "T4"
        assert result["gate_origin"] == "B22"
        assert result["terminal_destination"] == "T1"
        assert result["baggage_belt"] == "5"

    def test_parse_flight_data_partial_fields(self, client):
        """parse_flight_data debe manejar campos faltantes sin lanzar excepciones"""
        result = client.parse_flight_data(MOCK_PARTIAL_RAW)

        assert result["origin_iata"] == "MAD"
        assert result["destination_iata"] == "LHR"
        # Fields that are missing should be None, not raise
        assert result.get("airline_iata") is None
        assert result.get("aircraft_model") is None
        assert result.get("distance_km") is None

    def test_parse_flight_data_uses_great_circle_distance(self, client):
        result = client.parse_flight_data(MOCK_FLIGHT_RAW)
        assert result["distance_km"] == 621.5

    def test_parse_flight_data_haversine_fallback(self, client):
        """Si no hay greatCircleDistance pero hay coordenadas, usa Haversine"""
        raw = {**MOCK_FLIGHT_RAW}
        raw.pop("greatCircleDistance", None)
        result = client.parse_flight_data(raw)
        # Should compute via Haversine — MAD to BCN is ~483 km straight-line
        assert result["distance_km"] is not None
        assert result["distance_km"] > 0