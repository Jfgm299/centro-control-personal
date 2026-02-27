class TestAuth:

    def test_get_expenses_without_token_fails(self, client):
        response = client.get("/api/v1/expenses/")
        assert response.status_code == 401

    def test_create_expense_without_token_fails(self, client):
        response = client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 10.0, "account": "Revolut"})
        assert response.status_code == 401

    def test_get_expense_by_id_without_token_fails(self, client, auth_client, expense_id):
        response = client.get(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 401

    def test_update_expense_without_token_fails(self, client, auth_client, expense_id):
        response = client.patch(f"/api/v1/expenses/{expense_id}", json={"name": "Hack"})
        assert response.status_code == 401

    def test_delete_expense_without_token_fails(self, client, auth_client, expense_id):
        response = client.delete(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 401


class TestOwnership:

    def test_cannot_get_other_users_expense(self, auth_client, other_auth_client, expense_id):
        response = other_auth_client.get(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 404

    def test_cannot_update_other_users_expense(self, auth_client, other_auth_client, expense_id):
        response = other_auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"name": "Hack"})
        assert response.status_code == 404

    def test_cannot_delete_other_users_expense(self, auth_client, other_auth_client, expense_id):
        response = other_auth_client.delete(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 404

    def test_users_see_only_their_expenses(self, auth_client, other_auth_client, expense_id):
        other_auth_client.post("/api/v1/expenses/", json={"name": "Other", "quantity": 5.0, "account": "Revolut"})
        response = auth_client.get("/api/v1/expenses/")
        assert len(response.json()) == 1

    def test_other_user_expense_not_in_list(self, auth_client, other_auth_client):
        other_auth_client.post("/api/v1/expenses/", json={"name": "Other", "quantity": 5.0, "account": "Revolut"})
        response = auth_client.get("/api/v1/expenses/")
        assert response.json() == []


class TestGetExpenses:

    def test_get_expenses_empty(self, auth_client):
        response = auth_client.get("/api/v1/expenses/")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_expenses_returns_list(self, auth_client, expense_id):
        response = auth_client.get("/api/v1/expenses/")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_expenses_multiple(self, auth_client):
        auth_client.post("/api/v1/expenses/", json={"name": "Cafe", "quantity": 2.5, "account": "Revolut"})
        auth_client.post("/api/v1/expenses/", json={"name": "Gym", "quantity": 30.0, "account": "Imagin"})
        response = auth_client.get("/api/v1/expenses/")
        assert len(response.json()) == 2

    def test_get_expenses_response_fields(self, auth_client, expense_id):
        response = auth_client.get("/api/v1/expenses/")
        item = response.json()[0]
        assert "id" in item
        assert "name" in item
        assert "quantity" in item
        assert "account" in item
        assert "created_at" in item
        assert "updated_at" in item

    def test_get_expenses_both_accounts(self, auth_client):
        auth_client.post("/api/v1/expenses/", json={"name": "A", "quantity": 1.0, "account": "Revolut"})
        auth_client.post("/api/v1/expenses/", json={"name": "B", "quantity": 2.0, "account": "Imagin"})
        response = auth_client.get("/api/v1/expenses/")
        accounts = [e["account"] for e in response.json()]
        assert "Revolut" in accounts
        assert "Imagin" in accounts


class TestCreateExpense:

    def test_create_expense_revolut(self, auth_client):
        data = {"name": "Supermercado", "quantity": 45.50, "account": "Revolut"}
        response = auth_client.post("/api/v1/expenses/", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["name"] == "Supermercado"
        assert body["quantity"] == 45.50
        assert body["account"] == "Revolut"
        assert body["created_at"] is not None
        assert body["updated_at"] is None

    def test_create_expense_imagin(self, auth_client):
        data = {"name": "Netflix", "quantity": 12.99, "account": "Imagin"}
        response = auth_client.post("/api/v1/expenses/", json=data)
        assert response.status_code == 201
        assert response.json()["account"] == "Imagin"

    def test_create_expense_minimum_quantity(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Gominola", "quantity": 0.01, "account": "Revolut"})
        assert response.status_code == 201
        assert response.json()["quantity"] == 0.01

    def test_create_expense_large_quantity(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Coche", "quantity": 15000.0, "account": "Imagin"})
        assert response.status_code == 201
        assert response.json()["quantity"] == 15000.0

    def test_create_expense_max_name_length(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "A" * 100, "quantity": 1.0, "account": "Revolut"})
        assert response.status_code == 201

    def test_create_expense_zero_quantity_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 0.0, "account": "Revolut"})
        assert response.status_code == 422

    def test_create_expense_negative_quantity_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": -10.0, "account": "Revolut"})
        assert response.status_code == 422

    def test_create_expense_empty_name_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "", "quantity": 10.0, "account": "Revolut"})
        assert response.status_code == 422

    def test_create_expense_name_too_long_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "A" * 101, "quantity": 10.0, "account": "Revolut"})
        assert response.status_code == 422

    def test_create_expense_invalid_account_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 10.0, "account": "PayPal"})
        assert response.status_code == 422

    def test_create_expense_missing_name_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"quantity": 10.0, "account": "Revolut"})
        assert response.status_code == 422

    def test_create_expense_missing_quantity_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Test", "account": "Revolut"})
        assert response.status_code == 422

    def test_create_expense_missing_account_fails(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 10.0})
        assert response.status_code == 422

    def test_create_expense_ids_increment(self, auth_client):
        r1 = auth_client.post("/api/v1/expenses/", json={"name": "A", "quantity": 1.0, "account": "Revolut"})
        r2 = auth_client.post("/api/v1/expenses/", json={"name": "B", "quantity": 2.0, "account": "Revolut"})
        assert r2.json()["id"] > r1.json()["id"]

    def test_create_expense_decimal_quantity(self, auth_client):
        response = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 9.99, "account": "Imagin"})
        assert response.status_code == 201
        assert response.json()["quantity"] == 9.99


class TestGetExpenseById:

    def test_get_expense_success(self, auth_client, expense_id):
        response = auth_client.get(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 200
        assert response.json()["id"] == expense_id

    def test_get_expense_not_found(self, auth_client):
        response = auth_client.get("/api/v1/expenses/99999")
        assert response.status_code == 404

    def test_get_expense_correct_data(self, auth_client):
        created = auth_client.post("/api/v1/expenses/", json={"name": "Spotify", "quantity": 9.99, "account": "Revolut"})
        expense_id = created.json()["id"]
        response = auth_client.get(f"/api/v1/expenses/{expense_id}")
        body = response.json()
        assert body["name"] == "Spotify"
        assert body["quantity"] == 9.99
        assert body["account"] == "Revolut"

    def test_get_expense_response_fields(self, auth_client, expense_id):
        response = auth_client.get(f"/api/v1/expenses/{expense_id}")
        body = response.json()
        assert "id" in body
        assert "name" in body
        assert "quantity" in body
        assert "account" in body
        assert "created_at" in body
        assert "updated_at" in body

    def test_get_expense_updated_at_none_initially(self, auth_client, expense_id):
        response = auth_client.get(f"/api/v1/expenses/{expense_id}")
        assert response.json()["updated_at"] is None


class TestUpdateExpense:

    def test_update_name(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"name": "Updated Name"})
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    def test_update_quantity(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"quantity": 99.99})
        assert response.status_code == 200
        assert response.json()["quantity"] == 99.99

    def test_update_account_to_revolut(self, auth_client):
        created = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 5.0, "account": "Imagin"})
        expense_id = created.json()["id"]
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"account": "Revolut"})
        assert response.status_code == 200
        assert response.json()["account"] == "Revolut"

    def test_update_account_to_imagin(self, auth_client):
        created = auth_client.post("/api/v1/expenses/", json={"name": "Test", "quantity": 5.0, "account": "Revolut"})
        expense_id = created.json()["id"]
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"account": "Imagin"})
        assert response.status_code == 200
        assert response.json()["account"] == "Imagin"

    def test_update_all_fields(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}",
                                     json={"name": "New Name", "quantity": 99.0, "account": "Revolut"})
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "New Name"
        assert body["quantity"] == 99.0
        assert body["account"] == "Revolut"

    def test_update_sets_updated_at(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"name": "Updated"})
        assert response.json()["updated_at"] is not None

    def test_partial_update_preserves_other_fields(self, auth_client):
        created = auth_client.post("/api/v1/expenses/", json={"name": "Original", "quantity": 5.0, "account": "Imagin"})
        expense_id = created.json()["id"]
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"quantity": 10.0})
        body = response.json()
        assert body["name"] == "Original"
        assert body["account"] == "Imagin"
        assert body["quantity"] == 10.0

    def test_update_not_found(self, auth_client):
        response = auth_client.patch("/api/v1/expenses/99999", json={"name": "Test"})
        assert response.status_code == 404

    def test_update_invalid_account_fails(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"account": "Bizum"})
        assert response.status_code == 422

    def test_update_zero_quantity_fails(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"quantity": 0.0})
        assert response.status_code == 422

    def test_update_negative_quantity_fails(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"quantity": -5.0})
        assert response.status_code == 422

    def test_update_empty_name_fails(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"name": ""})
        assert response.status_code == 422

    def test_update_name_too_long_fails(self, auth_client, expense_id):
        response = auth_client.patch(f"/api/v1/expenses/{expense_id}", json={"name": "A" * 101})
        assert response.status_code == 422


class TestDeleteExpense:

    def test_delete_expense_success(self, auth_client, expense_id):
        response = auth_client.delete(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 204

    def test_delete_expense_removes_it(self, auth_client, expense_id):
        auth_client.delete(f"/api/v1/expenses/{expense_id}")
        response = auth_client.get(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 404

    def test_delete_expense_not_found(self, auth_client):
        response = auth_client.delete("/api/v1/expenses/99999")
        assert response.status_code == 404

    def test_delete_expense_twice_fails(self, auth_client, expense_id):
        auth_client.delete(f"/api/v1/expenses/{expense_id}")
        response = auth_client.delete(f"/api/v1/expenses/{expense_id}")
        assert response.status_code == 404

    def test_delete_one_expense_preserves_others(self, auth_client):
        r1 = auth_client.post("/api/v1/expenses/", json={"name": "A", "quantity": 1.0, "account": "Revolut"})
        r2 = auth_client.post("/api/v1/expenses/", json={"name": "B", "quantity": 2.0, "account": "Imagin"})
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]
        auth_client.delete(f"/api/v1/expenses/{id1}")
        response = auth_client.get("/api/v1/expenses/")
        remaining = response.json()
        assert len(remaining) == 1
        assert remaining[0]["id"] == id2

    def test_delete_expense_not_in_list(self, auth_client, expense_id):
        auth_client.delete(f"/api/v1/expenses/{expense_id}")
        response = auth_client.get("/api/v1/expenses/")
        assert response.json() == []