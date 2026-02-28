import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone


# ==================== TEST AUTH ====================

class TestAuth:

    def test_add_flight_without_token_fails(self, client):
        response = client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 401

    def test_get_flights_without_token_fails(self, client):
        response = client.get("/api/v1/flights/")
        assert response.status_code == 401

    def test_search_flight_without_token_fails(self, client):
        response = client.get("/api/v1/flights/search", params={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 401

    def test_get_passport_without_token_fails(self, client):
        response = client.get("/api/v1/flights/passport")
        assert response.status_code == 401

    def test_get_flight_by_id_without_token_fails(self, client, auth_client, created_flight_id):
        response = client.get(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 401

    def test_update_notes_without_token_fails(self, client, auth_client, created_flight_id):
        response = client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": "test"})
        assert response.status_code == 401

    def test_refresh_flight_without_token_fails(self, client, auth_client, created_flight_id):
        response = client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 401

    def test_delete_flight_without_token_fails(self, client, auth_client, created_flight_id):
        response = client.delete(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 401


# ==================== TEST OWNERSHIP ====================

class TestOwnership:

    def test_cannot_get_other_users_flight(self, auth_client, other_auth_client, created_flight_id):
        response = other_auth_client.get(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 404

    def test_cannot_delete_other_users_flight(self, auth_client, other_auth_client, created_flight_id):
        response = other_auth_client.delete(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 404

    def test_cannot_refresh_other_users_flight(self, auth_client, other_auth_client, created_flight_id):
        response = other_auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 404

    def test_cannot_update_notes_on_other_users_flight(self, auth_client, other_auth_client, created_flight_id):
        response = other_auth_client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": "hacked"})
        assert response.status_code == 404

    def test_users_see_only_their_flights(self, auth_client, other_auth_client, created_flight_id, mock_aerodatabox):
        other_auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        response = auth_client.get("/api/v1/flights/")
        assert len(response.json()) == 1


# ==================== TEST ADD FLIGHT ====================

class TestAddFlight:

    def test_add_flight_success(self, auth_client, mock_aerodatabox, past_flight_data):
        response = auth_client.post("/api/v1/flights/", json=past_flight_data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["flight_number"] == "VY1234"
        assert body["origin_iata"] == "MAD"
        assert body["destination_iata"] == "BCN"

    def test_add_flight_normalizes_to_uppercase(self, auth_client, mock_aerodatabox):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "vy1234", "flight_date": "2025-06-15"})
        assert response.status_code == 201
        assert response.json()["flight_number"] == "VY1234"

    def test_add_flight_duplicate_fails(self, auth_client, mock_aerodatabox, past_flight_data, created_flight_id):
        response = auth_client.post("/api/v1/flights/", json=past_flight_data)
        assert response.status_code == 409

    def test_add_flight_not_found_in_api(self, auth_client, mock_aerodatabox_not_found):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "XX9999", "flight_date": "2025-06-15"})
        assert response.status_code == 404

    def test_add_flight_missing_flight_number_fails(self, auth_client):
        response = auth_client.post("/api/v1/flights/", json={"flight_date": "2025-06-15"})
        assert response.status_code == 422

    def test_add_flight_missing_date_fails(self, auth_client):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234"})
        assert response.status_code == 422

    def test_add_flight_date_too_far_in_past_fails(self, auth_client):
        from datetime import date, timedelta
        old_date = (date.today() - timedelta(days=366)).isoformat()
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": old_date})
        assert response.status_code == 422

    def test_add_flight_date_too_far_in_future_fails(self, auth_client):
        from datetime import date, timedelta
        future_date = (date.today() + timedelta(days=366)).isoformat()
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": future_date})
        assert response.status_code == 422

    def test_add_flight_aerodatabox_timeout_returns_503(self, auth_client, mock_aerodatabox_timeout):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 503

    def test_add_flight_aerodatabox_rate_limit_returns_503(self, auth_client, mock_aerodatabox_rate_limit):
        response = auth_client.post("/api/v1/flights/", json={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 503

    def test_add_flight_stores_airline_info(self, auth_client, mock_aerodatabox, past_flight_data):
        response = auth_client.post("/api/v1/flights/", json=past_flight_data)
        body = response.json()
        assert body["airline_name"] == "Vueling"
        assert body["airline_iata"] == "VY"

    def test_add_flight_stores_aircraft_info(self, auth_client, mock_aerodatabox, past_flight_data):
        response = auth_client.post("/api/v1/flights/", json=past_flight_data)
        body = response.json()
        assert body["aircraft_model"] == "Airbus A320"
        assert body["aircraft_registration"] == "EC-MGY"

    def test_add_flight_stores_distance(self, auth_client, mock_aerodatabox, past_flight_data):
        response = auth_client.post("/api/v1/flights/", json=past_flight_data)
        assert response.json()["distance_km"] == 621.5

    def test_add_flight_past_is_marked_as_past(self, auth_client, mock_aerodatabox, past_flight_data):
        response = auth_client.post("/api/v1/flights/", json=past_flight_data)
        assert response.json()["is_past"] is True

    def test_add_flight_future_is_not_past(self, auth_client, mock_aerodatabox_future, future_flight_data):
        response = auth_client.post("/api/v1/flights/", json=future_flight_data)
        assert response.json()["is_past"] is False

    def test_add_flight_with_notes(self, auth_client, mock_aerodatabox):
        response = auth_client.post("/api/v1/flights/", json={
            "flight_number": "VY1234",
            "flight_date": "2025-06-15",
            "notes": "Family trip"
        })
        assert response.status_code == 201
        assert response.json()["notes"] == "Family trip"


# ==================== TEST GET FLIGHTS ====================

class TestGetFlights:

    def test_get_flights_empty(self, auth_client):
        response = auth_client.get("/api/v1/flights/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_flights_returns_list(self, auth_client, created_flight_id):
        response = auth_client.get("/api/v1/flights/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_flights_with_multiple(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_get_flights_filter_past(self, auth_client, created_flight_id, future_flight_id):
        response = auth_client.get("/api/v1/flights/", params={"past": True})
        assert response.status_code == 200
        flights = response.json()
        assert all(f["is_past"] is True for f in flights)

    def test_get_flights_filter_upcoming(self, auth_client, created_flight_id, future_flight_id):
        response = auth_client.get("/api/v1/flights/", params={"upcoming": True})
        assert response.status_code == 200
        flights = response.json()
        assert all(f["is_past"] is False for f in flights)

    def test_get_flights_pagination_limit(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/", params={"limit": 2})
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_flights_pagination_offset(self, auth_client, multiple_flights):
        response_all = auth_client.get("/api/v1/flights/")
        response_offset = auth_client.get("/api/v1/flights/", params={"offset": 2})
        assert len(response_offset.json()) == len(response_all.json()) - 2

    def test_get_flights_response_fields(self, auth_client, created_flight_id):
        response = auth_client.get("/api/v1/flights/")
        item = response.json()[0]
        for field in ["id", "flight_number", "flight_date", "origin_iata",
                      "destination_iata", "status", "is_past"]:
            assert field in item


# ==================== TEST GET FLIGHT BY ID ====================

class TestGetFlightById:

    def test_get_flight_success(self, auth_client, created_flight_id):
        response = auth_client.get(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 200
        assert response.json()["id"] == created_flight_id

    def test_get_flight_not_found(self, auth_client):
        response = auth_client.get("/api/v1/flights/99999")
        assert response.status_code == 404

    def test_get_flight_response_fields(self, auth_client, created_flight_id):
        response = auth_client.get(f"/api/v1/flights/{created_flight_id}")
        body = response.json()
        for field in ["id", "flight_number", "flight_date", "status", "origin_iata",
                      "destination_iata", "airline_name", "distance_km", "is_past", "created_at"]:
            assert field in body

    def test_get_flight_is_past_true_for_past_flight(self, auth_client, created_flight_id):
        response = auth_client.get(f"/api/v1/flights/{created_flight_id}")
        assert response.json()["is_past"] is True

    def test_get_flight_is_past_false_for_future_flight(self, auth_client, future_flight_id):
        response = auth_client.get(f"/api/v1/flights/{future_flight_id}")
        assert response.json()["is_past"] is False


# ==================== TEST DELETE FLIGHT ====================

class TestDeleteFlight:

    def test_delete_flight_success(self, auth_client, created_flight_id):
        response = auth_client.delete(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 204

    def test_delete_flight_not_found(self, auth_client):
        response = auth_client.delete("/api/v1/flights/99999")
        assert response.status_code == 404

    def test_delete_flight_removes_it(self, auth_client, created_flight_id):
        auth_client.delete(f"/api/v1/flights/{created_flight_id}")
        response = auth_client.get(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 404

    def test_delete_flight_twice_returns_404(self, auth_client, created_flight_id):
        auth_client.delete(f"/api/v1/flights/{created_flight_id}")
        response = auth_client.delete(f"/api/v1/flights/{created_flight_id}")
        assert response.status_code == 404


# ==================== TEST REFRESH FLIGHT ====================

def _bypass_throttle(auth_client, flight_id):
    """Helper: pone last_refreshed_at a 10 min atrás para saltarse el throttle"""
    from app.modules.flights_tracker.flight import Flight
    from app.main import app
    from app.core import get_db

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    flight.last_refreshed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.commit()


class TestRefreshFlight:

    def test_refresh_flight_immediate_throttled(self, auth_client, created_flight_id, mock_aerodatabox):
        """Refresh inmediato tras crear el vuelo siempre da 429 — add_flight setea last_refreshed_at"""
        response = auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 429

    def test_refresh_flight_not_found(self, auth_client, mock_aerodatabox):
        response = auth_client.post("/api/v1/flights/99999/refresh")
        assert response.status_code == 404

    def test_refresh_flight_after_cooldown_succeeds(self, auth_client, created_flight_id, mock_aerodatabox):
        _bypass_throttle(auth_client, created_flight_id)
        response = auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 200

    def test_refresh_flight_returns_flight_response(self, auth_client, created_flight_id, mock_aerodatabox):
        _bypass_throttle(auth_client, created_flight_id)
        response = auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 200
        body = response.json()
        assert "id" in body
        assert "flight_number" in body
        assert "status" in body

    def test_refresh_flight_updates_last_refreshed_at(self, auth_client, created_flight_id, mock_aerodatabox):
        from app.modules.flights_tracker.flight import Flight
        from app.main import app
        from app.core import get_db

        _bypass_throttle(auth_client, created_flight_id)
        before = datetime.now(timezone.utc) - timedelta(minutes=10)

        auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")

        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        flight = db.query(Flight).filter(Flight.id == created_flight_id).first()
        assert flight.last_refreshed_at > before

    def test_refresh_flight_aerodatabox_timeout_after_cooldown_returns_503(
        self, auth_client, created_flight_id, mock_aerodatabox_timeout
    ):
        _bypass_throttle(auth_client, created_flight_id)
        response = auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 503

    def test_refresh_flight_throttle_check_before_api_call(self, auth_client, created_flight_id, mock_aerodatabox_timeout):
        """El throttle se comprueba ANTES de llamar a la API — da 429 sin llegar al timeout"""
        response = auth_client.post(f"/api/v1/flights/{created_flight_id}/refresh")
        assert response.status_code == 429


# ==================== TEST UPDATE NOTES ====================

class TestUpdateNotes:

    def test_update_notes_success(self, auth_client, created_flight_id):
        response = auth_client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": "Great flight!"})
        assert response.status_code == 200
        assert response.json()["notes"] == "Great flight!"

    def test_update_notes_too_long_fails(self, auth_client, created_flight_id):
        response = auth_client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": "x" * 501})
        assert response.status_code == 422

    def test_update_notes_clear_with_none(self, auth_client, created_flight_id):
        auth_client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": "Some note"})
        response = auth_client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": None})
        assert response.status_code == 200
        assert response.json()["notes"] is None

    def test_update_notes_not_found(self, auth_client):
        response = auth_client.patch("/api/v1/flights/99999/notes", json={"notes": "test"})
        assert response.status_code == 404

    def test_update_notes_only_changes_notes(self, auth_client, created_flight_id):
        before = auth_client.get(f"/api/v1/flights/{created_flight_id}").json()
        auth_client.patch(f"/api/v1/flights/{created_flight_id}/notes", json={"notes": "New note"})
        after = auth_client.get(f"/api/v1/flights/{created_flight_id}").json()
        assert after["origin_iata"] == before["origin_iata"]
        assert after["destination_iata"] == before["destination_iata"]
        assert after["notes"] == "New note"


# ==================== TEST SEARCH FLIGHT ====================

class TestSearchFlight:

    def test_search_flight_success(self, auth_client, mock_aerodatabox):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 200
        body = response.json()
        assert body["flight_number"] == "VY1234"

    def test_search_flight_not_found(self, auth_client, mock_aerodatabox_not_found):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "XX9999", "flight_date": "2025-06-15"})
        assert response.status_code == 404

    def test_search_flight_missing_flight_number_fails(self, auth_client):
        response = auth_client.get("/api/v1/flights/search", params={"flight_date": "2025-06-15"})
        assert response.status_code == 422

    def test_search_flight_missing_date_fails(self, auth_client):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "VY1234"})
        assert response.status_code == 422

    def test_search_flight_response_has_no_id(self, auth_client, mock_aerodatabox):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert "id" not in response.json()

    def test_search_flight_response_has_no_created_at(self, auth_client, mock_aerodatabox):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert "created_at" not in response.json()

    def test_search_flight_timeout_returns_503(self, auth_client, mock_aerodatabox_timeout):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 503

    def test_search_flight_rate_limit_returns_503(self, auth_client, mock_aerodatabox_rate_limit):
        response = auth_client.get("/api/v1/flights/search", params={"flight_number": "VY1234", "flight_date": "2025-06-15"})
        assert response.status_code == 503