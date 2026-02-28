import pytest


class TestPassport:

    def test_passport_empty_user(self, auth_client):
        """Usuario sin vuelos no debe lanzar excepción"""
        response = auth_client.get("/api/v1/flights/passport")
        assert response.status_code == 200
        body = response.json()
        assert body["total_flights"] == 0
        assert body["total_distance_km"] == 0.0
        assert body["countries_visited"] == []
        assert body["airports_top"] == []

    def test_passport_total_flights(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        assert response.json()["total_flights"] == 5

    def test_passport_total_distance(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        body = response.json()
        assert body["total_distance_km"] > 0

    def test_passport_countries_visited(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        countries = response.json()["countries_visited"]
        assert isinstance(countries, list)
        assert len(countries) > 0
        for country in countries:
            assert "country_code" in country
            assert "visit_count" in country

    def test_passport_airports_top(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        airports = response.json()["airports_top"]
        assert isinstance(airports, list)
        assert len(airports) > 0
        for ap in airports:
            assert "iata" in ap
            assert "flight_count" in ap

    def test_passport_airlines_top(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        airlines = response.json()["airlines_top"]
        assert isinstance(airlines, list)
        assert len(airlines) > 0
        for airline in airlines:
            assert "flight_count" in airline

    def test_passport_flights_by_year(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        by_year = response.json()["flights_by_year"]
        assert isinstance(by_year, list)
        assert len(by_year) > 0
        for entry in by_year:
            assert "year" in entry
            assert "flight_count" in entry
            assert "total_distance_km" in entry

    def test_passport_delay_report(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        delay = response.json()["delay_report"]
        assert "total_hours_lost" in delay
        assert "worst_delay_minutes" in delay
        assert "on_time_percentage" in delay

    def test_passport_longest_flight(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        longest = response.json()["longest_flight"]
        assert longest is not None
        assert "flight_number" in longest

    def test_passport_current_streak(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        body = response.json()
        assert "current_streak_days" in body
        assert isinstance(body["current_streak_days"], int)
        assert body["current_streak_days"] >= 0

    def test_passport_aircraft_stats(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        aircraft = response.json()["aircraft_stats"]
        assert isinstance(aircraft, list)
        for a in aircraft:
            assert "model" in a
            assert "flight_count" in a

    def test_passport_next_flight(self, auth_client, created_flight_id, future_flight_id):
        response = auth_client.get("/api/v1/flights/passport")
        next_flight = response.json()["next_flight"]
        assert next_flight is not None
        assert next_flight["is_past"] is False

    def test_passport_avg_distance(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        body = response.json()
        assert "avg_flight_distance_km" in body
        if body["total_flights"] > 0:
            assert body["avg_flight_distance_km"] > 0

    def test_passport_unique_counts(self, auth_client, multiple_flights):
        response = auth_client.get("/api/v1/flights/passport")
        body = response.json()
        assert "unique_airports_count" in body
        assert "unique_countries_count" in body
        assert "unique_airlines_count" in body
        assert body["unique_airports_count"] >= 0
        assert body["unique_countries_count"] >= 0

    def test_passport_response_fields_complete(self, auth_client, created_flight_id):
        response = auth_client.get("/api/v1/flights/passport")
        assert response.status_code == 200
        body = response.json()
        expected_fields = [
            "total_flights", "total_distance_km", "total_duration_hours",
            "countries_visited", "airports_top", "airlines_top", "aircraft_stats",
            "flights_by_year", "delay_report", "longest_flight", "shortest_flight",
            "most_recent_flight", "next_flight", "first_flight_date",
            "current_streak_days", "unique_airports_count", "unique_countries_count",
            "unique_aircraft_count", "unique_airlines_count",
            "avg_flight_distance_km", "avg_flight_duration_hours"
        ]
        for field in expected_fields:
            assert field in body, f"Missing field: {field}"