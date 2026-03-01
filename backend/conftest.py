# backend/conftest.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Carga .env.test si existe, antes de importar nada de la app
load_dotenv(Path(__file__).parent / ".env.test", override=True)

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.core import Base, get_db
from app.main import app
from app.core.module_loader import get_all_schemas

# URL independiente — no usa settings.DATABASE_URL
SQLALCHEMY_TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://test:test@db_test:5432/test_db"  # default dentro de Docker
)
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



@pytest.fixture(scope="session", autouse=True)
def fast_password_hashing():
    import bcrypt
    with patch("bcrypt.gensalt", return_value=bcrypt.gensalt(rounds=4)):
        yield


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS core CASCADE"))
        for schema in get_all_schemas():
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        conn.execute(text("CREATE SCHEMA core"))
        for schema in get_all_schemas():
            conn.execute(text(f"CREATE SCHEMA {schema}"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(setup_database):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Truncate cascading desde users — limpia todo automáticamente
        with engine.begin() as conn:
            conn.execute(text(
                "TRUNCATE TABLE core.users RESTART IDENTITY CASCADE"
            ))


def make_db_override(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    return override_get_db


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(db):
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={
            "email": "test@test.com", "username": "testuser", "password": "testpassword"
        })
        token = c.post("/api/v1/auth/login", json={
            "email": "test@test.com", "password": "testpassword"
        }).json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def other_auth_client(db):
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={
            "email": "other@test.com", "username": "otheruser", "password": "testpassword"
        })
        token = c.post("/api/v1/auth/login", json={
            "email": "other@test.com", "password": "testpassword"
        }).json()["access_token"]
        c.headers.update({"Authorization": f"Bearer {token}"})
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client_with_refresh(db):
    app.dependency_overrides[get_db] = make_db_override(db)
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={
            "email": "test@test.com", "username": "testuser", "password": "testpassword"
        })
        data = c.post("/api/v1/auth/login", json={
            "email": "test@test.com", "password": "testpassword"
        }).json()
        c.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        c.refresh_token = data["refresh_token"]
        yield c
    app.dependency_overrides.clear()