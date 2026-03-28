# Testing

## Conftest Hierarchy

```
backend/
├── conftest.py                          ← root conftest — fixtures globales
└── app/modules/gym_tracker/tests/
        └── conftest.py                  ← module conftest — fixtures específicas del módulo
```

El root conftest define todo lo relacionado con la infraestructura de tests. Los conftest de módulo solo añaden fixtures de datos específicos del módulo.

## Root Conftest — Fixtures Globales (`backend/conftest.py`)

| Fixture | Scope | Qué hace |
|---------|-------|----------|
| `fast_password_hashing` | session | Parchea bcrypt a rounds=4 para que los tests sean rápidos |
| `setup_database` | session | Crea todos los schemas y tablas al inicio; las elimina al final |
| `db` | function | Abre sesión DB; al terminar, hace TRUNCATE CASCADE desde `core.users` |
| `client` | function | TestClient sin autenticar |
| `auth_client` | function | TestClient autenticado como `test@test.com` |
| `other_auth_client` | function | TestClient autenticado como `other@test.com` (para tests de ownership) |
| `auth_client_with_refresh` | function | Como `auth_client` pero también expone `refresh_token` |

**Estrategia de limpieza:** `TRUNCATE TABLE core.users RESTART IDENTITY CASCADE` — al borrar el usuario, se eliminan en cascada todos sus datos en todos los schemas. No hay que truncar tabla por tabla.

## Module Conftest Pattern

```python
# app/modules/gym_tracker/tests/conftest.py
import pytest

@pytest.fixture
def sample_workout_data():
    return {"notes": "Test workout"}

# Recursos se crean via API, no directamente en BD
@pytest.fixture
def active_workout_id(auth_client):
    response = auth_client.post("/api/v1/workouts/", json={"notes": "Test"})
    assert response.status_code == 201, response.json()
    return response.json()["id"]

# Fixtures encadenadas — el setup refleja el flujo real de la app
@pytest.fixture
def weight_exercise_id(auth_client, active_workout_id, sample_exercise_data):
    response = auth_client.post(
        f"/api/v1/workouts/{active_workout_id}/exercises",
        json=sample_exercise_data
    )
    assert response.status_code == 201, response.json()
    return response.json()["id"]
```

## Cómo Correr Tests

```bash
# Suite completa
docker-compose exec api pytest

# Todos los tests de un módulo
docker-compose exec api pytest app/modules/gym_tracker/tests -v

# Un archivo específico
docker-compose exec api pytest app/modules/calendar_tracker/tests/test_sync.py -v

# Una clase o función específica
docker-compose exec api pytest app/modules/calendar_tracker/tests/test_sync.py::TestAppleIntegration -v
docker-compose exec api pytest app/modules/calendar_tracker/tests/test_sync.py::TestAppleIntegration::test_sync_creates_events -v

# Con output de print statements
docker-compose exec api pytest app/modules/gym_tracker/tests -v -s
```

**Servicio:** siempre `api`, no `backend`. Comando: `docker-compose` con guión, no `docker compose`.

## Lo Que NO Hay Que Hacer

- **No crear objetos ORM directamente en tests** — siempre usar el `auth_client` y las APIs. Esto garantiza que los tests prueben el flujo real y que la limpieza CASCADE funcione correctamente.
- **No usar `scope="session"` para fixtures de datos** — solo para infraestructura (`setup_database`, `fast_password_hashing`). Los datos van en `scope="function"` para que cada test empiece limpio.
- **No abrir sesiones DB manuales** — usar el fixture `db` del root conftest.
- **No hardcodear IDs** — usar los fixtures encadenados para obtener IDs reales tras la creación.
