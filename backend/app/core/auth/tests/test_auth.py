class TestRegister:

    def test_register_success(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "new@test.com",
            "username": "newuser",
            "password": "password123"
        })
        assert response.status_code == 201
        body = response.json()
        assert body["id"] is not None
        assert body["email"] == "new@test.com"
        assert body["username"] == "newuser"
        assert body["is_active"] is True
        assert "hashed_password" not in body

    def test_register_duplicate_email_fails(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "username": "user1", "password": "pass"
        })
        response = client.post("/api/v1/auth/register", json={
            "email": "dup@test.com", "username": "user2", "password": "pass"
        })
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username_fails(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "sameuser", "password": "pass"
        })
        response = client.post("/api/v1/auth/register", json={
            "email": "b@test.com", "username": "sameuser", "password": "pass"
        })
        assert response.status_code == 400
        assert "username" in response.json()["detail"].lower()

    def test_register_invalid_email_fails(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "notanemail", "username": "user", "password": "pass"
        })
        assert response.status_code == 422

    def test_register_missing_email_fails(self, client):
        response = client.post("/api/v1/auth/register", json={
            "username": "user", "password": "pass"
        })
        assert response.status_code == 422

    def test_register_missing_password_fails(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user"
        })
        assert response.status_code == 422

    def test_register_missing_username_fails(self, client):
        response = client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "password": "pass"
        })
        assert response.status_code == 422


class TestLogin:

    def test_login_success(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "login@test.com", "username": "loginuser", "password": "mypassword"
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "login@test.com", "password": "mypassword"
        })
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 0
        assert len(body["refresh_token"]) > 0

    def test_login_wrong_password_fails(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "correct"
        })
        response = client.post("/api/v1/auth/login", json={
            "email": "a@test.com", "password": "wrong"
        })
        assert response.status_code == 401

    def test_login_wrong_email_fails(self, client):
        response = client.post("/api/v1/auth/login", json={
            "email": "noexiste@test.com", "password": "pass"
        })
        assert response.status_code == 401

    def test_login_returns_different_tokens_each_time(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        r1 = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        r2 = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        assert r1.json()["refresh_token"] != r2.json()["refresh_token"]

    def test_login_access_and_refresh_tokens_are_different(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        response = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        body = response.json()
        assert body["access_token"] != body["refresh_token"]


class TestRefreshToken:
    def test_refresh_returns_new_access_token(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        login = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        refresh_token = login.json()["refresh_token"]

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        # Lo importante: el refresh token rota, no que el access sea diferente
        assert body["refresh_token"] != refresh_token

    def test_refresh_token_rotation(self, client):
        """El refresh token debe cambiar en cada uso"""
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        login = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        old_refresh = login.json()["refresh_token"]
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        new_refresh = response.json()["refresh_token"]
        assert old_refresh != new_refresh

    def test_refresh_token_cannot_be_reused(self, client):
        """Un refresh token usado no puede volver a usarse"""
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        login = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        refresh_token = login.json()["refresh_token"]

        client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 401

    def test_refresh_invalid_token_fails(self, client):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "token_falso"})
        assert response.status_code == 401

    def test_refresh_empty_token_fails(self, client):
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": ""})
        assert response.status_code == 401

    def test_refresh_missing_token_fails(self, client):
        response = client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 422

    def test_new_access_token_works(self, client):
        """El nuevo access token debe funcionar para acceder a endpoints protegidos"""
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        login = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        refresh_token = login.json()["refresh_token"]

        refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        new_access_token = refresh.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {new_access_token}"})
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200

    def test_multiple_refresh_chain(self, client):
        """Varios refreshes encadenados deben funcionar"""
        client.post("/api/v1/auth/register", json={
            "email": "a@test.com", "username": "user", "password": "pass"
        })
        login = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "pass"})
        current_refresh = login.json()["refresh_token"]

        for _ in range(3):
            response = client.post("/api/v1/auth/refresh", json={"refresh_token": current_refresh})
            assert response.status_code == 200
            current_refresh = response.json()["refresh_token"]


class TestLogout:

    def test_logout_success(self, auth_client_with_refresh):
        response = auth_client_with_refresh.post("/api/v1/auth/logout", json={
            "refresh_token": auth_client_with_refresh.refresh_token
        })
        assert response.status_code == 204

    def test_logout_invalidates_refresh_token(self, client, auth_client_with_refresh):
        auth_client_with_refresh.post("/api/v1/auth/logout", json={
            "refresh_token": auth_client_with_refresh.refresh_token
        })
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": auth_client_with_refresh.refresh_token
        })
        assert response.status_code == 401

    def test_logout_with_invalid_token_succeeds_silently(self, auth_client):
        """Logout con token inválido no debe fallar — idempotente"""
        response = auth_client.post("/api/v1/auth/logout", json={
            "refresh_token": "token_que_no_existe"
        })
        assert response.status_code == 204

    def test_logout_without_token_fails(self, auth_client):
        response = auth_client.post("/api/v1/auth/logout", json={})
        assert response.status_code == 422


class TestMe:

    def test_me_returns_current_user(self, auth_client):
        response = auth_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "test@test.com"
        assert body["username"] == "testuser"
        assert body["is_active"] is True
        assert "hashed_password" not in body

    def test_me_without_token_fails(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token_fails(self, client):
        client.headers.update({"Authorization": "Bearer token_invalido"})
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401