import pytest
from unittest.mock import patch, AsyncMock
from datetime import date, datetime, timedelta, timezone

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


# ── Fixtures para automation contract ─────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_flights_dispatch_cache():
    """Limpia el cache de deduplicación del scheduler entre tests."""
    from app.modules.flights_tracker import scheduler_service
    scheduler_service._departing_soon_cache.clear()
    yield
    scheduler_service._departing_soon_cache.clear()


def _make_departing_soon_mock_raw():
    """Raw flight data con scheduled_departure en ~24 horas."""
    departure_dt = datetime.now(timezone.utc) + timedelta(hours=24)
    arrival_dt   = departure_dt + timedelta(hours=1, minutes=15)
    dep_local    = departure_dt.strftime("%Y-%m-%d %H:%M+00:00")
    arr_local    = arrival_dt.strftime("%Y-%m-%d %H:%M+00:00")
    flight_date  = departure_dt.strftime("%Y-%m-%d")
    return {
        "number": "VY9999", "status": "Expected",
        "greatCircleDistance": {"km": 621.5, "mile": 386.2, "nm": 335.6, "meter": 621500, "feet": 2038700},
        "departure": {
            "airport": {"iata": "MAD", "icao": "LEMD", "name": "Madrid Barajas",
                        "municipalityName": "Madrid", "countryCode": "ES",
                        "timeZone": "UTC", "location": {"lat": 40.4719, "lon": -3.5626}},
            "scheduledTime": {"local": dep_local, "utc": departure_dt.strftime("%Y-%m-%d %H:%MZ")},
            "terminal": "T4", "gate": "B22", "quality": ["Basic"]
        },
        "arrival": {
            "airport": {"iata": "BCN", "icao": "LEBL", "name": "Barcelona El Prat",
                        "municipalityName": "Barcelona", "countryCode": "ES",
                        "timeZone": "UTC", "location": {"lat": 41.2971, "lon": 2.0785}},
            "scheduledTime": {"local": arr_local},
            "terminal": "T1", "quality": ["Basic"]
        },
        "airline": {"iata": "VY", "icao": "VLG", "name": "Vueling"},
        "aircraft": {"model": "Airbus A320", "reg": "EC-MGY", "modeS": "3443C2"},
        "lastUpdatedUtc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "codeshareStatus": "IsOperator", "isCargo": False
    }


@pytest.fixture
def mock_aerodatabox_departing_soon():
    with patch(
        "app.modules.flights_tracker.aerodatabox_client.AeroDataBoxClient.get_flight",
        new_callable=AsyncMock, return_value=_make_departing_soon_mock_raw()
    ):
        yield


@pytest.fixture
def departing_soon_flight_date():
    return (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%d")


@pytest.fixture
def departing_soon_flight_id(auth_client, mock_aerodatabox_departing_soon, departing_soon_flight_date):
    response = auth_client.post(
        "/api/v1/flights/",
        json={"flight_number": "VY9999", "flight_date": departing_soon_flight_date}
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]


# ── Fixtures de automatizaciones ──────────────────────────────────────────────

@pytest.fixture(autouse=True, scope="session")
def register_flights_triggers():
    """Registra los triggers y acciones de flights_tracker en el registry."""
    from app.modules.automations_engine.core.registry import registry

    registry.register_trigger(
        module_id="flights_tracker",
        trigger_id="flight_added",
        label="Vuelo registrado",
        config_schema={},
        handler="app.modules.flights_tracker.automation_handlers.handle_flight_added",
    )
    registry.register_trigger(
        module_id="flights_tracker",
        trigger_id="flight_status_changed",
        label="Estado del vuelo cambió",
        config_schema={},
        handler="app.modules.flights_tracker.automation_handlers.handle_flight_status_changed",
    )
    registry.register_trigger(
        module_id="flights_tracker",
        trigger_id="flight_departing_soon",
        label="Vuelo sale pronto",
        config_schema={},
        handler="app.modules.flights_tracker.automation_handlers.handle_flight_departing_soon",
    )
    registry.register_action(
        module_id="flights_tracker",
        action_id="get_flight_details",
        label="Obtener detalles del vuelo",
        config_schema={},
        handler="app.modules.flights_tracker.automation_handlers.action_get_flight_details",
    )
    registry.register_action(
        module_id="flights_tracker",
        action_id="refresh_flight",
        label="Actualizar datos del vuelo",
        config_schema={},
        handler="app.modules.flights_tracker.automation_handlers.action_refresh_flight",
    )
    yield


@pytest.fixture
def automation_for_flight_added(auth_client):
    """Automatización suscrita a flights_tracker.flight_added."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto flight added",
        "trigger_type": "module_event",
        "trigger_ref":  "flights_tracker.flight_added",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "flights_tracker.flight_added"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "flights_tracker.get_flight_details"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def automation_for_flight_status_changed(auth_client):
    """Automatización suscrita a flights_tracker.flight_status_changed (sin filtro de estado)."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto flight status changed",
        "trigger_type": "module_event",
        "trigger_ref":  "flights_tracker.flight_status_changed",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {"trigger_id": "flights_tracker.flight_status_changed"}},
                {"id": "n2", "type": "action",  "config": {"action_id": "flights_tracker.get_flight_details"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def automation_for_flight_status_arrived(auth_client):
    """Automatización suscrita a flight_status_changed filtrando solo to_status=arrived."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto flight arrived",
        "trigger_type": "module_event",
        "trigger_ref":  "flights_tracker.flight_status_changed",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {
                    "trigger_id": "flights_tracker.flight_status_changed",
                    "to_status":  "arrived",
                }},
                {"id": "n2", "type": "action",  "config": {"action_id": "flights_tracker.get_flight_details"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]


@pytest.fixture
def automation_for_flight_departing_soon(auth_client):
    """Automatización suscrita a flights_tracker.flight_departing_soon (24h)."""
    r = auth_client.post("/api/v1/automations/", json={
        "name":         "Auto flight departing soon",
        "trigger_type": "module_event",
        "trigger_ref":  "flights_tracker.flight_departing_soon",
        "flow": {
            "nodes": [
                {"id": "n1", "type": "trigger", "config": {
                    "trigger_id":   "flights_tracker.flight_departing_soon",
                    "hours_before": 24,
                }},
                {"id": "n2", "type": "action",  "config": {"action_id": "flights_tracker.get_flight_details"}},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
        },
    })
    assert r.status_code == 201, r.json()
    return r.json()["id"]