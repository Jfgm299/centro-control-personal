import pytest
from unittest.mock import patch, AsyncMock
from datetime import date, timedelta

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


def _make_future_mock_raw():
    future_local = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") + " 10:00+02:00"
    future_arr   = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d") + " 11:15+02:00"
    return {
        "number": "VY1234", "status": "Expected",
        "greatCircleDistance": {"km": 621.5, "mile": 386.2, "nm": 335.6, "meter": 621500, "feet": 2038700},
        "departure": {
            "airport": {"iata": "MAD", "icao": "LEMD", "name": "Madrid Barajas",
                        "municipalityName": "Madrid", "countryCode": "ES",
                        "timeZone": "Europe/Madrid", "location": {"lat": 40.4719, "lon": -3.5626}},
            "scheduledTime": {"local": future_local}, "terminal": "T4", "gate": "B22", "quality": ["Basic"]
        },
        "arrival": {
            "airport": {"iata": "BCN", "icao": "LEBL", "name": "Barcelona El Prat",
                        "municipalityName": "Barcelona", "countryCode": "ES",
                        "timeZone": "Europe/Madrid", "location": {"lat": 41.2971, "lon": 2.0785}},
            "scheduledTime": {"local": future_arr}, "terminal": "T1", "quality": ["Basic"]
        },
        "airline": {"iata": "VY", "icao": "VLG", "name": "Vueling"},
        "aircraft": {"model": "Airbus A320", "reg": "EC-MGY", "modeS": "3443C2"},
        "lastUpdatedUtc": "2026-02-28T09:30:00Z", "codeshareStatus": "IsOperator", "isCargo": False
    }


@pytest.fixture
def mock_aerodatabox():
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock, return_value=MOCK_FLIGHT_RAW
    ):
        yield

@pytest.fixture
def mock_aerodatabox_not_found():
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock, side_effect=FlightNotFoundInAPIError("XX9999", "2025-06-15")
    ):
        yield

@pytest.fixture
def mock_aerodatabox_timeout():
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock, side_effect=AeroDataBoxTimeoutError()
    ):
        yield

@pytest.fixture
def mock_aerodatabox_rate_limit():
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock, side_effect=AeroDataBoxRateLimitError()
    ):
        yield

@pytest.fixture
def mock_aerodatabox_future():
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock, return_value=_make_future_mock_raw()
    ):
        yield

@pytest.fixture
def past_flight_data():
    return {"flight_number": "VY1234", "flight_date": "2025-06-15"}

@pytest.fixture
def future_flight_data():
    return {"flight_number": "VY1234", "flight_date": (date.today() + timedelta(days=30)).isoformat()}

@pytest.fixture
def created_flight_id(auth_client, mock_aerodatabox, past_flight_data):
    response = auth_client.post("/api/v1/flights/", json=past_flight_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def future_flight_id(auth_client, mock_aerodatabox_future, future_flight_data):
    response = auth_client.post("/api/v1/flights/", json=future_flight_data)
    assert response.status_code == 201, response.json()
    return response.json()["id"]

@pytest.fixture
def multiple_flights(auth_client, mock_aerodatabox):
    past_dates = [(date.today() - timedelta(days=30 * i)).isoformat() for i in range(1, 6)]
    flight_numbers = ["VY1234", "IB3456", "VY5678", "FR9012", "IB7890"]
    ids = []
    for fn, fd in zip(flight_numbers, past_dates):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": fn, "flight_date": fd})
        assert response.status_code == 201, response.json()
        ids.append(response.json()["id"])
    return ids