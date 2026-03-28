# flights_tracker

Schema: `flights_tracker` | Automation contract: ✅

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
├── manifest.py               ← get_settings() para AeroDataBox keys
├── models.py
├── flight.py                 ← modelo Flight + FlightStatus enum
├── flight_schema.py
├── flight_router.py
├── aerodatabox_client.py     ← cliente HTTP a AeroDataBox API
├── automation_registry.py    ← registra triggers y acciones
├── automation_handlers.py    ← implementaciones de handlers + _flight_to_dict()
├── automation_dispatcher.py  ← conecta eventos con el motor
├── scheduler_service.py      ← job horario (APScheduler)
├── services/
│   ├── flight_service.py     ← hooks dispatcher en add_flight() y refresh_flight()
│   └── passport_service.py
├── exceptions.py
├── handlers/
└── tests/
```

## Automation Contract Implementation

### Triggers registrados

| trigger_ref | Cuándo dispara | Cómo se detecta |
|-------------|---------------|-----------------|
| `flights_tracker.flight_added` | Al registrar un vuelo | Hook en `flight_service.add_flight()` después de `db.refresh()` |
| `flights_tracker.flight_status_changed` | Cuando el estado del vuelo cambia al refrescar | Hook en `flight_service.refresh_flight()`: captura `old_status` antes del refresh y compara con `new_status` después |
| `flights_tracker.flight_departing_soon` | N horas antes de la salida programada | Job horario del scheduler; deduplicación por `(flight_id, hours_before, "YYYY-MM-DD")` |

### Acciones registradas

| action_ref | Qué hace |
|------------|----------|
| `flights_tracker.get_flight_details` | Devuelve info completa del vuelo como contexto (`flight_id` de config o payload) |
| `flights_tracker.refresh_flight` | Refresca datos del vuelo via AeroDataBox; maneja `FlightRefreshThrottleError` → `{"done": False, "reason": "throttled"}` |

### Scheduler

`scheduler_service.py` registra un job horario vía APScheduler, arrancado en `startup_event` desde `main.py`:

| Job | Frecuencia | Qué hace |
|-----|-----------|----------|
| `job_check_flight_departing_soon` | Horaria (`:00`) | Itera automations activas con `trigger_ref=flights_tracker.flight_departing_soon`, extrae `hours_before` de config, busca vuelos en ventana `±30min` alrededor de `now + hours_before` |

Deduplicación en memoria: `(flight_id, hours_before, "YYYY-MM-DD")` → una vez por día.

### Nota técnica: action_refresh_flight es async

`flight_service.refresh_flight()` es async. Los action handlers son sync. Solución:

```python
loop = asyncio.new_event_loop()
try:
    flight = loop.run_until_complete(flight_service.refresh_flight(db, user_id, flight_id))
finally:
    loop.close()
```

Funciona porque los handlers se ejecutan fuera del event loop de FastAPI (en el executor del flow_executor).

### Tests

No llamar `job_check_flight_departing_soon()` directamente en tests — usa `SessionLocal()` que apunta al DB de dev (5432), no al test DB (5433). En su lugar, llamar `dispatcher.on_flight_departing_soon()` con la sesión de test.
