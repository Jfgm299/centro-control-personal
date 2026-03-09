# flights_tracker

Schema: `flights_tracker` | Automation contract: ❌

Módulo de seguimiento de vuelos. Permite registrar vuelos y consultar su estado en tiempo real mediante la API AeroDataBox.

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `Flight` | `flights_tracker.flights` | Vuelo registrado por el usuario |

## User Relationships

```python
user.flights  # List[Flight]
```

## Key Business Logic

- `FlightStatus` enum cubre estados activos (`expected`, `check_in`, `boarding`, `gate_closed`, `departed`, `en_route`, `approaching`, `delayed`) y finales (`arrived`, `canceled`, `diverted`, `canceled_uncertain`).
- Los datos de vuelo se enriquecen desde **AeroDataBox API**.

## External Dependencies

- **AeroDataBox API** (vía RapidAPI)
  - `AERODATABOX_API_KEY` — requerida
  - `AERODATABOX_BASE_URL` — default: `https://aerodatabox.p.rapidapi.com`
  - `AERODATABOX_HOST` — default: `aerodatabox.p.rapidapi.com`

> **Nota Railway:** `manifest.get_settings()` usa `os.environ` como fuente primaria. pydantic-settings v2 no lee vars no declaradas del entorno del sistema. Ver patrón en `patterns.md`.

## Structure

```
flights_tracker/
├── manifest.py           ← get_settings() para AeroDataBox keys
├── models.py
├── flight.py             ← modelo Flight + FlightStatus enum
├── flight_schema.py
├── flight_router.py
├── aerodatabox_client.py ← cliente HTTP a AeroDataBox API
├── services/
│   ├── flight_service.py
│   └── passport_service.py
├── exceptions.py
├── handlers/
└── tests/
```
