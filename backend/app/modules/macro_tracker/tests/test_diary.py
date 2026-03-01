from datetime import date, timedelta
import pytest


class TestDiaryAuth:

    def test_add_entry_without_token_fails(self, client):
        response = client.post("/api/v1/macros/diary", json={})
        assert response.status_code == 401

    def test_get_diary_without_token_fails(self, client):
        response = client.get("/api/v1/macros/diary")
        assert response.status_code == 401

    def test_get_summary_without_token_fails(self, client):
        response = client.get("/api/v1/macros/diary/summary")
        assert response.status_code == 401


class TestDiaryOwnership:

    def test_cannot_update_other_users_entry(
        self, auth_client, other_auth_client, diary_entry_id
    ):
        response = other_auth_client.patch(
            f"/api/v1/macros/diary/{diary_entry_id}/amount",
            json={"amount_g": 200.0},
        )
        assert response.status_code == 404

    def test_cannot_delete_other_users_entry(
        self, auth_client, other_auth_client, diary_entry_id
    ):
        response = other_auth_client.delete(f"/api/v1/macros/diary/{diary_entry_id}")
        assert response.status_code == 404

    def test_users_see_only_their_entries(
        self, auth_client, other_auth_client, mock_off_client, sample_barcode
    ):
        product_id = auth_client.get(
            f"/api/v1/macros/products/barcode/{sample_barcode}"
        ).json()["id"]

        auth_client.post("/api/v1/macros/diary", json={
            "product_id": product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        other_auth_client.post("/api/v1/macros/diary", json={
            "product_id": product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "dinner",
            "amount_g": 200.0,
        })

        response = auth_client.get("/api/v1/macros/diary")
        assert len(response.json()) == 1


class TestAddDiaryEntry:

    def test_add_entry_success(self, auth_client, cached_product_id):
        data = {
            "product_id": cached_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 150.0,
        }
        response = auth_client.post("/api/v1/macros/diary", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["product_id"]  == cached_product_id
        assert body["meal_type"]   == "lunch"
        assert body["amount_g"]    == 150.0
        assert body["product"]     is not None

    def test_add_entry_calculates_nutrients(self, auth_client, cached_product_id):
        """150g de arroz (354 kcal/100g) → 531 kcal"""
        data = {
            "product_id": cached_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "breakfast",
            "amount_g": 150.0,
        }
        body = auth_client.post("/api/v1/macros/diary", json=data).json()
        assert body["energy_kcal"]    == pytest.approx(531.0,  abs=0.1)
        assert body["proteins_g"]     == pytest.approx(10.5,   abs=0.1)
        assert body["carbohydrates_g"] == pytest.approx(115.5, abs=0.1)
        assert body["fat_g"]          == pytest.approx(1.35,   abs=0.1)

    def test_add_entry_partial_product_nulls_ok(self, auth_client, partial_product_id):
        """Producto sin grasas — los nutrientes nulos se guardan como null, no 0"""
        data = {
            "product_id": partial_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "other",
            "amount_g": 100.0,
        }
        body = auth_client.post("/api/v1/macros/diary", json=data).json()
        assert body["energy_kcal"] == 200.0
        assert body["fat_g"]       is None
        assert body["proteins_g"]  is None

    def test_add_entry_invalid_product_fails(self, auth_client):
        data = {
            "product_id": 99999,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        }
        response = auth_client.post("/api/v1/macros/diary", json=data)
        assert response.status_code == 404

    def test_add_entry_zero_amount_fails(self, auth_client, cached_product_id):
        data = {
            "product_id": cached_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 0.0,
        }
        response = auth_client.post("/api/v1/macros/diary", json=data)
        assert response.status_code == 422

    def test_add_entry_negative_amount_fails(self, auth_client, cached_product_id):
        data = {
            "product_id": cached_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": -50.0,
        }
        response = auth_client.post("/api/v1/macros/diary", json=data)
        assert response.status_code == 422

    def test_add_entry_invalid_meal_type_fails(self, auth_client, cached_product_id):
        data = {
            "product_id": cached_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "brunch",
            "amount_g": 100.0,
        }
        response = auth_client.post("/api/v1/macros/diary", json=data)
        assert response.status_code == 422

    def test_add_same_product_twice_same_day(self, auth_client, cached_product_id):
        """El mismo producto puede añadirse varias veces el mismo día"""
        data = {
            "product_id": cached_product_id,
            "entry_date": date.today().isoformat(),
            "meal_type": "lunch",
            "amount_g": 100.0,
        }
        r1 = auth_client.post("/api/v1/macros/diary", json=data)
        r2 = auth_client.post("/api/v1/macros/diary", json=data)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]

    def test_add_all_meal_types(self, auth_client, cached_product_id):
        meal_types = ["breakfast", "morning_snack", "lunch",
                      "afternoon_snack", "dinner", "other"]
        for mt in meal_types:
            resp = auth_client.post("/api/v1/macros/diary", json={
                "product_id": cached_product_id,
                "entry_date": date.today().isoformat(),
                "meal_type": mt,
                "amount_g": 100.0,
            })
            assert resp.status_code == 201, f"meal_type '{mt}' falló: {resp.json()}"


class TestUpdateDiaryEntry:

    def test_update_amount_recalculates_nutrients(self, auth_client, diary_entry_id):
        """Cambiar de 150g a 200g debe recalcular kcal: 354 * 200/100 = 708"""
        response = auth_client.patch(
            f"/api/v1/macros/diary/{diary_entry_id}/amount",
            json={"amount_g": 200.0},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["amount_g"]    == 200.0
        assert body["energy_kcal"] == pytest.approx(708.0, abs=0.1)

    def test_update_amount_zero_fails(self, auth_client, diary_entry_id):
        response = auth_client.patch(
            f"/api/v1/macros/diary/{diary_entry_id}/amount",
            json={"amount_g": 0.0},
        )
        assert response.status_code == 422

    def test_update_notes(self, auth_client, diary_entry_id):
        response = auth_client.patch(
            f"/api/v1/macros/diary/{diary_entry_id}/notes",
            json={"notes": "Con sal y aceite"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Con sal y aceite"

    def test_update_notes_to_null(self, auth_client, diary_entry_id):
        auth_client.patch(
            f"/api/v1/macros/diary/{diary_entry_id}/notes",
            json={"notes": "Temporal"},
        )
        response = auth_client.patch(
            f"/api/v1/macros/diary/{diary_entry_id}/notes",
            json={"notes": None},
        )
        assert response.status_code == 200
        assert response.json()["notes"] is None

    def test_update_nonexistent_entry_fails(self, auth_client):
        response = auth_client.patch(
            "/api/v1/macros/diary/99999/amount",
            json={"amount_g": 100.0},
        )
        assert response.status_code == 404


class TestDeleteDiaryEntry:

    def test_delete_entry_success(self, auth_client, diary_entry_id):
        response = auth_client.delete(f"/api/v1/macros/diary/{diary_entry_id}")
        assert response.status_code == 204

    def test_delete_removes_entry(self, auth_client, diary_entry_id):
        auth_client.delete(f"/api/v1/macros/diary/{diary_entry_id}")
        response = auth_client.get("/api/v1/macros/diary")
        ids = [e["id"] for e in response.json()]
        assert diary_entry_id not in ids

    def test_delete_twice_fails(self, auth_client, diary_entry_id):
        auth_client.delete(f"/api/v1/macros/diary/{diary_entry_id}")
        response = auth_client.delete(f"/api/v1/macros/diary/{diary_entry_id}")
        assert response.status_code == 404

    def test_delete_nonexistent_fails(self, auth_client):
        response = auth_client.delete("/api/v1/macros/diary/99999")
        assert response.status_code == 404


class TestDailySummary:

    def test_summary_empty_day(self, auth_client):
        response = auth_client.get(
            f"/api/v1/macros/diary/summary?date={date.today().isoformat()}"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["meals"]  == []
        assert body["totals"]["energy_kcal"] == 0.0
        assert body["goals"]  is not None    # se crean con defaults

    def test_summary_groups_by_meal(self, auth_client, cached_product_id):
        today = date.today().isoformat()
        for meal in ["breakfast", "lunch", "dinner"]:
            auth_client.post("/api/v1/macros/diary", json={
                "product_id": cached_product_id,
                "entry_date": today,
                "meal_type": meal,
                "amount_g": 100.0,
            })
        body = auth_client.get(f"/api/v1/macros/diary/summary?date={today}").json()
        meal_types = [m["meal_type"] for m in body["meals"]]
        assert "breakfast" in meal_types
        assert "lunch"     in meal_types
        assert "dinner"    in meal_types

    def test_summary_totals_sum_correctly(self, auth_client, cached_product_id):
        today = date.today().isoformat()
        # 2 entradas de 100g = 200g → 708 kcal
        for _ in range(2):
            auth_client.post("/api/v1/macros/diary", json={
                "product_id": cached_product_id,
                "entry_date": today,
                "meal_type": "lunch",
                "amount_g": 100.0,
            })
        body = auth_client.get(f"/api/v1/macros/diary/summary?date={today}").json()
        assert body["totals"]["energy_kcal"] == pytest.approx(708.0, abs=0.1)

    def test_summary_includes_progress(self, auth_client, cached_product_id):
        today = date.today().isoformat()
        auth_client.post("/api/v1/macros/diary", json={
            "product_id": cached_product_id,
            "entry_date": today,
            "meal_type": "lunch",
            "amount_g": 100.0,
        })
        body = auth_client.get(f"/api/v1/macros/diary/summary?date={today}").json()
        assert body["progress"] is not None
        assert "energy_pct"   in body["progress"]
        assert "proteins_pct" in body["progress"]


class TestGoals:

    def test_get_goals_creates_defaults(self, auth_client):
        response = auth_client.get("/api/v1/macros/goals")
        assert response.status_code == 200
        body = response.json()
        assert body["energy_kcal"]     == 2000.0
        assert body["proteins_g"]      == 150.0
        assert body["carbohydrates_g"] == 250.0
        assert body["fat_g"]           == 65.0

    def test_get_goals_idempotent(self, auth_client):
        """Llamar dos veces devuelve el mismo id"""
        r1 = auth_client.get("/api/v1/macros/goals")
        r2 = auth_client.get("/api/v1/macros/goals")
        assert r1.json()["id"] == r2.json()["id"]

    def test_update_goals(self, auth_client):
        response = auth_client.put("/api/v1/macros/goals", json={
            "energy_kcal": 2500.0,
            "proteins_g":  180.0,
        })
        assert response.status_code == 200
        body = response.json()
        assert body["energy_kcal"] == 2500.0
        assert body["proteins_g"]  == 180.0
        # Los no enviados se conservan
        assert body["carbohydrates_g"] == 250.0

    def test_update_goals_negative_fails(self, auth_client):
        response = auth_client.put("/api/v1/macros/goals", json={"energy_kcal": -100.0})
        assert response.status_code == 422

    def test_goals_are_per_user(self, auth_client, other_auth_client):
        auth_client.put("/api/v1/macros/goals", json={"energy_kcal": 3000.0})
        response = other_auth_client.get("/api/v1/macros/goals")
        assert response.json()["energy_kcal"] == 2000.0  # defaults del otro usuario