import pytest


class TestApiKeysAuth:

    def test_list_without_token_fails(self, client):
        assert client.get("/api/v1/automations/api-keys/").status_code == 401

    def test_create_without_token_fails(self, client, api_key_data):
        assert client.post("/api/v1/automations/api-keys/", json=api_key_data).status_code == 401

    def test_revoke_without_token_fails(self, client, auth_client, api_key_id_and_token):
        key_id, _ = api_key_id_and_token
        assert client.delete(f"/api/v1/automations/api-keys/{key_id}").status_code == 401


class TestApiKeysOwnership:

    def test_cannot_revoke_other_users_key(self, auth_client, other_auth_client, api_key_id_and_token):
        key_id, _ = api_key_id_and_token
        assert other_auth_client.delete(
            f"/api/v1/automations/api-keys/{key_id}"
        ).status_code == 404

    def test_users_see_only_their_keys(self, auth_client, other_auth_client, api_key_id_and_token):
        other_auth_client.post("/api/v1/automations/api-keys/", json={
            "name": "Other key", "scopes": ["read"]
        })
        response = auth_client.get("/api/v1/automations/api-keys/")
        assert len(response.json()) == 1


class TestCreateApiKey:

    def test_create_success(self, auth_client, api_key_data):
        response = auth_client.post("/api/v1/automations/api-keys/", json=api_key_data)
        assert response.status_code == 201
        body = response.json()
        assert body["token"] is not None
        assert body["token"].startswith("ak_live_")
        assert body["key_prefix"] == body["token"][:8]
        assert "read"    in body["scopes"]
        assert "trigger" in body["scopes"]

    def test_create_token_only_returned_once(self, auth_client, api_key_data):
        create_resp = auth_client.post("/api/v1/automations/api-keys/", json=api_key_data)
        key_id = create_resp.json()["id"]
        list_resp = auth_client.get("/api/v1/automations/api-keys/")
        listed_key = next(k for k in list_resp.json() if k["id"] == key_id)
        assert "token" not in listed_key

    def test_create_with_automation_scope(self, auth_client, automation_id):
        response = auth_client.post("/api/v1/automations/api-keys/", json={
            "name":          "Scoped key",
            "automation_id": automation_id,
            "scopes":        ["trigger"],
        })
        assert response.status_code == 201
        assert response.json()["automation_id"] == automation_id

    def test_create_empty_name_fails(self, auth_client):
        assert auth_client.post("/api/v1/automations/api-keys/", json={
            "name": "", "scopes": ["read"]
        }).status_code == 422

    def test_create_invalid_scope_fails(self, auth_client):
        assert auth_client.post("/api/v1/automations/api-keys/", json={
            "name": "Bad scope", "scopes": ["admin"]
        }).status_code == 422

    def test_create_generates_unique_tokens(self, auth_client):
        r1 = auth_client.post("/api/v1/automations/api-keys/", json={"name": "K1", "scopes": ["read"]})
        r2 = auth_client.post("/api/v1/automations/api-keys/", json={"name": "K2", "scopes": ["read"]})
        assert r1.json()["token"] != r2.json()["token"]

    def test_create_with_expiry(self, auth_client):
        response = auth_client.post("/api/v1/automations/api-keys/", json={
            "name":       "Expiring key",
            "scopes":     ["read"],
            "expires_at": "2099-01-01T00:00:00Z",
        })
        assert response.status_code == 201
        assert response.json()["expires_at"] is not None


class TestListApiKeys:

    def test_list_empty(self, auth_client):
        assert auth_client.get("/api/v1/automations/api-keys/").json() == []

    def test_list_returns_created(self, auth_client, api_key_id_and_token):
        response = auth_client.get("/api/v1/automations/api-keys/")
        assert len(response.json()) == 1

    def test_list_response_fields(self, auth_client, api_key_id_and_token):
        key = auth_client.get("/api/v1/automations/api-keys/").json()[0]
        for field in ["id", "name", "key_prefix", "scopes", "is_active", "created_at"]:
            assert field in key

    def test_list_does_not_include_hash(self, auth_client, api_key_id_and_token):
        key = auth_client.get("/api/v1/automations/api-keys/").json()[0]
        assert "key_hash" not in key
        assert "token"    not in key


class TestRevokeApiKey:

    def test_revoke_success(self, auth_client, api_key_id_and_token):
        key_id, _ = api_key_id_and_token
        assert auth_client.delete(f"/api/v1/automations/api-keys/{key_id}").status_code == 204

    def test_revoke_removes_from_list(self, auth_client, api_key_id_and_token):
        key_id, _ = api_key_id_and_token
        auth_client.delete(f"/api/v1/automations/api-keys/{key_id}")
        keys = auth_client.get("/api/v1/automations/api-keys/").json()
        assert all(k["id"] != key_id for k in keys)

    def test_revoke_nonexistent_fails(self, auth_client):
        assert auth_client.delete("/api/v1/automations/api-keys/99999").status_code == 404

    def test_revoke_twice_fails(self, auth_client, api_key_id_and_token):
        key_id, _ = api_key_id_and_token
        auth_client.delete(f"/api/v1/automations/api-keys/{key_id}")
        assert auth_client.delete(
            f"/api/v1/automations/api-keys/{key_id}"
        ).status_code == 404


class TestRegistryEndpoints:

    def test_get_triggers(self, auth_client):
        response = auth_client.get("/api/v1/automations/registry/triggers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_actions(self, auth_client):
        response = auth_client.get("/api/v1/automations/registry/actions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_triggers_by_module(self, auth_client):
        response = auth_client.get("/api/v1/automations/registry/triggers/by-module")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_actions_by_module(self, auth_client):
        response = auth_client.get("/api/v1/automations/registry/actions/by-module")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_registry_requires_auth(self, client):
        assert client.get("/api/v1/automations/registry/triggers").status_code == 401
        assert client.get("/api/v1/automations/registry/actions").status_code == 401

    def test_triggers_have_required_fields(self, auth_client):
        triggers = auth_client.get("/api/v1/automations/registry/triggers").json()
        for t in triggers:
            assert "ref_id"        in t
            assert "module_id"     in t
            assert "label"         in t
            assert "config_schema" in t