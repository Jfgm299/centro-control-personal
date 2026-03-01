from datetime import date
import pytest


class TestStats:

    def test_stats_empty_returns_zeros(self, auth_client):
        response = auth_client.get("/api/v1/macros/stats?days=30")
        assert response.status_code == 200
        body = response.json()
        assert body["days_logged"]   == 0
        assert body["total_entries"] == 0
        assert body["consistency_pct"] == 0.0

    def test_stats_with_entries(self, auth_client, multiple_diary_entries):
        response = auth_client.get("/api/v1/macros/stats?days=30")
        assert response.status_code == 200
        body = response.json()
        assert body["days_logged"]   > 0
        assert body["total_entries"] == len(multiple_diary_entries)

    def test_stats_response_fields(self, auth_client, multiple_diary_entries):
        body = auth_client.get("/api/v1/macros/stats?days=30").json()
        assert "period_days"      in body
        assert "days_logged"      in body
        assert "total_entries"    in body
        assert "consistency_pct"  in body
        assert "daily_average"    in body
        assert "top_products"     in body

    def test_stats_daily_average_fields(self, auth_client, multiple_diary_entries):
        body = auth_client.get("/api/v1/macros/stats?days=30").json()
        avg = body["daily_average"]
        for field in ["avg_energy_kcal", "avg_proteins_g",
                      "avg_carbohydrates_g", "avg_fat_g", "avg_fiber_g"]:
            assert field in avg, f"Campo '{field}' ausente en daily_average"

    def test_stats_top_products(self, auth_client, multiple_diary_entries):
        body = auth_client.get("/api/v1/macros/stats?days=30").json()
        assert len(body["top_products"]) >= 1
        top = body["top_products"][0]
        assert "product"     in top
        assert "entry_count" in top
        assert top["entry_count"] > 0

    def test_stats_consistency_pct_range(self, auth_client, multiple_diary_entries):
        body = auth_client.get("/api/v1/macros/stats?days=30").json()
        assert 0.0 <= body["consistency_pct"] <= 100.0

    def test_stats_days_param_validation(self, auth_client):
        assert auth_client.get("/api/v1/macros/stats?days=6").status_code   == 422
        assert auth_client.get("/api/v1/macros/stats?days=366").status_code == 422
        assert auth_client.get("/api/v1/macros/stats?days=7").status_code   == 200
        assert auth_client.get("/api/v1/macros/stats?days=365").status_code == 200

    def test_stats_period_matches_param(self, auth_client):
        body = auth_client.get("/api/v1/macros/stats?days=14").json()
        assert body["period_days"] == 14