# ✈️ Flights Tracker

Módulo de registro y seguimiento de vuelos personales con enriquecimiento automático de datos vía AeroDataBox. Inspirado en el [Flighty Passport](https://www.flightyapp.com/) — el equivalente a un "Spotify Wrapped" del viajero frecuente.

## ¿Qué hace?

Permite registrar vuelos pasados y futuros proporcionando únicamente el número de vuelo y la fecha. El sistema llama automáticamente a AeroDataBox **una sola vez**, extrae y persiste todos los datos relevantes (aeropuertos, aerolínea, horarios, distancia, avión, estado) y a partir de ese momento opera de forma completamente autónoma sin llamadas adicionales a la API externa.

Incluye un **Pasaporte de vuelos** con estadísticas agregadas: kilómetros volados, países visitados, aerolíneas más usadas, aeropuertos favoritos, horas perdidas en retrasos, aviones volados y mucho más.

---

## Instalación

Añade el módulo a `INSTALLED_MODULES` en tu configuración:

```python
# core/config.py
INSTALLED_MODULES = [
    "flights_tracker",
    # otros módulos...
]
```

Añade las variables de entorno necesarias:

```env
# .env
AERODATABOX_API_KEY=tu_api_key
AERODATABOX_BASE_URL=https://aerodatabox.p.rapidapi.com
AERODATABOX_HOST=aerodatabox.p.rapidapi.com
```

Añade la dependencia HTTP:

```bash
pip install httpx>=0.27.0
```

Aplica la migración:

```bash
docker-compose exec api alembic upgrade head
```

Para desactivarlo, comenta o elimina la línea de `INSTALLED_MODULES`. El resto de módulos no se verá afectado.

---

## API externa — AeroDataBox

El módulo usa [AeroDataBox](https://rapidapi.com/aedbx-aedbx/api/aerodatabox) vía RapidAPI o API.Market.

| Plan | Precio | Llamadas |
|------|--------|----------|
| Free | $0 | 300 calls/mes (API.Market) |
| Basic | $0.99/mes | 600 calls/mes (RapidAPI) |

### Principio de mínimas llamadas

| Operación | Llamadas a AeroDataBox |
|-----------|----------------------|
| `POST /flights/` — añadir vuelo | 1 |
| `GET /flights/search` — previsualizar | 1 |
| `POST /{id}/refresh` — refrescar datos | 1 (throttle 5 min) |
| `GET /flights/` y todos los demás | **0** |

---

## Endpoints

Base URL: `/api/v1/flights`

| Método | Ruta | Status | Descripción | API call |
|--------|------|--------|-------------|----------|
| `POST` | `/` | 201 | Añadir vuelo | ⚡ 1 |
| `GET` | `/` | 200 | Listar vuelos paginados | — |
| `GET` | `/search` | 200 | Buscar vuelo sin guardar | ⚡ 1 |
| `GET` | `/passport` | 200 | Pasaporte completo de vuelos | — |
| `GET` | `/{flight_id}` | 200 | Obtener vuelo por ID | — |
| `PATCH` | `/{flight_id}/notes` | 200 | Actualizar notas personales | — |
| `POST` | `/{flight_id}/refresh` | 200 | Refrescar datos desde AeroDataBox | ⚡ 1 |
| `DELETE` | `/{flight_id}` | 204 | Eliminar vuelo | — |

> ⚠️ **Orden crítico de rutas**: `/search` y `/passport` están declaradas antes de `/{flight_id}` en el router para evitar que FastAPI interprete las rutas literales como parámetros.

---

## Modelos

### Flight

| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| `id` | `int` | — | Identificador único (PK) |
| `user_id` | `int` | — | FK a `core.users.id` (CASCADE DELETE) |
| `flight_number` | `str(10)` | — | Normalizado a UPPERCASE (IB3456) |
| `flight_date` | `date` | — | Fecha de salida en hora local del origen |
| `status` | `FlightStatus` | — | Estado actual del vuelo |
| `origin_iata` | `str(4)` | — | Código IATA aeropuerto origen |
| `origin_icao` | `str(5)` | ✓ | Código ICAO aeropuerto origen |
| `origin_name` | `str(200)` | ✓ | Nombre completo del aeropuerto |
| `origin_city` | `str(100)` | ✓ | Ciudad de origen |
| `origin_country_code` | `str(3)` | ✓ | Código ISO-2 país (ES, FR...) |
| `origin_timezone` | `str(50)` | ✓ | Timezone Olson (Europe/Madrid) |
| `origin_lat` | `float` | ✓ | Latitud del aeropuerto origen |
| `origin_lon` | `float` | ✓ | Longitud del aeropuerto origen |
| `destination_iata` | `str(4)` | — | Código IATA aeropuerto destino |
| `destination_*` | — | ✓ | Mismos campos que origen para destino |
| `airline_iata` | `str(3)` | ✓ | Código IATA aerolínea (IB, VY...) |
| `airline_icao` | `str(4)` | ✓ | Código ICAO aerolínea |
| `airline_name` | `str(100)` | ✓ | Nombre de la aerolínea |
| `scheduled_departure` | `datetime(TZ)` | ✓ | Salida programada |
| `revised_departure` | `datetime(TZ)` | ✓ | Salida revisada oficial |
| `predicted_departure` | `datetime(TZ)` | ✓ | Predicción de salida |
| `actual_departure` | `datetime(TZ)` | ✓ | Salida real (runwayTime) |
| `scheduled_arrival` | `datetime(TZ)` | ✓ | Llegada programada |
| `revised_arrival` | `datetime(TZ)` | ✓ | Llegada revisada oficial |
| `predicted_arrival` | `datetime(TZ)` | ✓ | Predicción de llegada |
| `actual_arrival` | `datetime(TZ)` | ✓ | Llegada real (runwayTime) |
| `duration_minutes` | `int` | ✓ | Duración calculada en minutos |
| `delay_departure_minutes` | `int` | ✓ | Retraso en salida |
| `delay_arrival_minutes` | `int` | ✓ | Retraso en llegada |
| `distance_km` | `float` | ✓ | Distancia great-circle (o Haversine fallback) |
| `aircraft_model` | `str(100)` | ✓ | Modelo (Airbus A320, Boeing 737...) |
| `aircraft_registration` | `str(20)` | ✓ | Matrícula (EC-MCS) |
| `aircraft_icao24` | `str(10)` | ✓ | Mode-S ICAO 24-bit |
| `terminal_origin` | `str(10)` | ✓ | Terminal de salida |
| `gate_origin` | `str(10)` | ✓ | Puerta de embarque |
| `terminal_destination` | `str(10)` | ✓ | Terminal de llegada |
| `baggage_belt` | `str(10)` | ✓ | Cinta de equipajes |
| `is_past` | `bool` | — | True si el vuelo ya ha ocurrido |
| `is_diverted` | `bool` | — | True si fue desviado |
| `notes` | `text` | ✓ | Notas personales del usuario |
| `last_refreshed_at` | `datetime(TZ)` | ✓ | Última vez que se refrescó desde la API |
| `created_at` | `datetime(TZ)` | — | server_default=now() |
| `updated_at` | `datetime(TZ)` | ✓ | onupdate=now() |

### FlightStatus (enum)

| Valor | Descripción |
|-------|-------------|
| `expected` | Programado / esperado |
| `check_in` | Check-in abierto |
| `boarding` | Embarque en progreso |
| `gate_closed` | Puerta cerrada |
| `departed` | Ha despegado |
| `en_route` | En vuelo |
| `approaching` | En aproximación |
| `delayed` | Retrasado |
| `arrived` | Ha aterrizado |
| `canceled` | Cancelado |
| `diverted` | Desviado a otro aeropuerto |
| `canceled_uncertain` | Estado incierto, posiblemente cancelado |
| `unknown` | Estado no disponible |

---

## Schemas Pydantic

### FlightCreate — input del usuario

| Campo | Tipo | Requerido | Validación |
|-------|------|-----------|------------|
| `flight_number` | `str` | ✅ | Normalizado a UPPERCASE automáticamente |
| `flight_date` | `date` | ✅ | Rango ±1 año desde hoy |
| `notes` | `str` | — | Opcional, max 500 chars |

### FlightUpdate — PATCH notes

| Campo | Tipo | Validación |
|-------|------|------------|
| `notes` | `str \| None` | Max 500 chars. `None` limpia las notas existentes |

### FlightResponse — output completo

Incluye todos los campos del modelo excepto `user_id`. Todos los campos de AeroDataBox son opcionales (un vuelo puede tener datos parciales).

### FlightSearchResponse — búsqueda sin guardar

Igual que `FlightResponse` pero sin `id`, `created_at`, `notes` ni `is_past`. Representa datos de la API sin persistir.

---

## Pasaporte de vuelos

El pasaporte calcula estadísticas agregadas de todos los vuelos del usuario en Python puro, sin llamadas externas. Una sola query a BD, todo el cálculo en memoria.

### PassportResponse

| Campo | Descripción |
|-------|-------------|
| `total_flights` | Total de vuelos pasados |
| `total_distance_km` | Kilómetros totales volados |
| `total_duration_hours` | Horas totales en el aire |
| `avg_flight_distance_km` | Distancia media por vuelo |
| `avg_flight_duration_hours` | Duración media por vuelo |
| `unique_countries_count` | Países únicos visitados |
| `unique_airports_count` | Aeropuertos únicos visitados |
| `unique_airlines_count` | Aerolíneas distintas usadas |
| `unique_aircraft_count` | Modelos de avión distintos |
| `countries_visited` | Lista de países con conteo y ciudades |
| `airports_top` | Top 10 aeropuertos por frecuencia |
| `airlines_top` | Top 10 aerolíneas con avg delay |
| `aircraft_stats` | Top 10 aviones con distancia total |
| `flights_by_year` | Estadísticas agrupadas por año |
| `longest_flight` | Vuelo más largo (por distancia) |
| `shortest_flight` | Vuelo más corto (por distancia) |
| `most_recent_flight` | Vuelo más reciente |
| `next_flight` | Próximo vuelo futuro registrado |
| `first_flight_date` | Fecha del primer vuelo registrado |
| `current_streak_days` | Días consecutivos con vuelo hasta hoy |
| `delay_report` | Análisis completo de retrasos |

### DelayReport

| Campo | Descripción |
|-------|-------------|
| `total_hours_lost` | Total de horas perdidas por retrasos |
| `worst_delay_minutes` | Peor retraso en minutos |
| `worst_delay_flight` | Vuelo con el peor retraso |
| `on_time_percentage` | % de vuelos con ≤15 min de retraso |
| `pct_flights_delayed` | % de vuelos con >15 min de retraso |

---

## Ejemplos de uso

### Añadir un vuelo

```http
POST /api/v1/flights/
Authorization: Bearer <token>
Content-Type: application/json

{
  "flight_number": "VY1234",
  "flight_date": "2026-03-15"
}
```

### Respuesta

```json
{
  "id": 1,
  "flight_number": "VY1234",
  "flight_date": "2026-03-15",
  "status": "expected",
  "origin_iata": "MAD",
  "origin_name": "Madrid Barajas",
  "origin_city": "Madrid",
  "origin_country_code": "ES",
  "destination_iata": "BCN",
  "destination_name": "Barcelona El Prat",
  "destination_city": "Barcelona",
  "destination_country_code": "ES",
  "airline_name": "Vueling",
  "airline_iata": "VY",
  "aircraft_model": "Airbus A320",
  "distance_km": 621.5,
  "scheduled_departure": "2026-03-15T10:00:00+02:00",
  "scheduled_arrival": "2026-03-15T11:15:00+02:00",
  "duration_minutes": 75,
  "is_past": false,
  "is_diverted": false,
  "notes": null,
  "created_at": "2026-02-28T12:00:00Z"
}
```

### Listar vuelos pasados paginados

```http
GET /api/v1/flights/?past=true&limit=10&offset=0
Authorization: Bearer <token>
```

### Buscar vuelo sin guardar

```http
GET /api/v1/flights/search?flight_number=IB3456&flight_date=2026-03-20
Authorization: Bearer <token>
```

### Añadir notas a un vuelo

```http
PATCH /api/v1/flights/1/notes
Authorization: Bearer <token>
Content-Type: application/json

{
  "notes": "Viaje de trabajo a Barcelona. Asiento 14A."
}
```

### Refrescar datos de un vuelo

```http
POST /api/v1/flights/1/refresh
Authorization: Bearer <token>
```

> ⚠️ Throttle de 5 minutos entre refreshes. Devuelve 429 si se reintenta antes.

### Consultar el pasaporte

```http
GET /api/v1/flights/passport
Authorization: Bearer <token>
```

---

## Autenticación y ownership

Todos los endpoints requieren JWT válido (`Authorization: Bearer <token>`). Sin token → **401**.

El ownership se aplica filtrando siempre `Flight.user_id == user.id`. Si el vuelo no existe **o** pertenece a otro usuario → **404**. Nunca se devuelve 403 para no revelar si un recurso existe.

---

## Errores

| Excepción | HTTP | Cuándo ocurre |
|-----------|------|---------------|
| `FlightNotFoundInAPIError` | 404 | Vuelo no existe en AeroDataBox para esa fecha/número |
| `FlightAlreadyExistsError` | 409 | El usuario ya tiene ese `flight_number + flight_date` registrado |
| `FlightNotFoundError` | 404 | El `flight_id` no existe en BD o no pertenece al usuario |
| `AeroDataBoxTimeoutError` | 503 | AeroDataBox no responde en 10 segundos |
| `AeroDataBoxRateLimitError` | 503 | Rate limit alcanzado (429 de AeroDataBox) |
| `AeroDataBoxError` | 503 | Error genérico de AeroDataBox (5xx) |
| `FlightRefreshThrottleError` | 429 | Refresh intentado menos de 5 minutos después del anterior |

---

## Estructura del módulo

```
flights_tracker/
├── __init__.py               # Exporta router, TAGS, TAG_GROUP
├── flight.py                 # Modelo SQLAlchemy + enum FlightStatus
├── flight_schema.py          # Schemas Pydantic (Create, Response, Update, Passport...)
├── flight_router.py          # Endpoints FastAPI (orden crítico de rutas)
├── aerodatabox_client.py     # Cliente HTTP para AeroDataBox (httpx)
├── exceptions.py             # Excepciones específicas del módulo
├── services/
│   ├── __init__.py
│   ├── flight_service.py     # Lógica de negocio (async)
│   └── passport_service.py   # Cálculos del pasaporte (Python puro)
└── tests/
    ├── __init__.py
    ├── conftest.py           # Fixtures y mocks del módulo
    ├── test_flights.py       # Tests principales (57 tests)
    ├── test_passport.py      # Tests del pasaporte (15 tests)
    └── test_aerodatabox_client.py  # Tests del cliente (8 tests)
```

---

## Tests

```bash
# Ejecutar solo los tests de este módulo
docker-compose exec api pytest app/modules/flights_tracker/tests/ -v

# Ejecutar todos los tests del proyecto
docker-compose exec api pytest
```

### Cobertura — 80 tests nuevos

| Clase | Tests |
|-------|-------|
| `TestAuth` | 8 |
| `TestOwnership` | 5 |
| `TestAddFlight` | 15 |
| `TestGetFlights` | 8 |
| `TestGetFlightById` | 5 |
| `TestDeleteFlight` | 4 |
| `TestRefreshFlight` | 7 |
| `TestUpdateNotes` | 5 |
| `TestSearchFlight` | 8 |
| `TestPassport` | 15 |
| `TestAeroDataBoxClient` | 8 |
| **Total** | **88** |

> CERO llamadas reales a AeroDataBox en los tests — todo mockeado con `AsyncMock`. Los fixtures `mock_aerodatabox` y `mock_aerodatabox_future` parchean `AeroDataBoxClient.get_flight` con datos estáticos.

---

## Dependencias

- `httpx>=0.27.0` — cliente HTTP async para llamadas a AeroDataBox
- `pytest-asyncio` — soporte para tests async (requiere `asyncio_mode = auto` en `pytest.ini`)
- `app.core.database` — `Base`, `get_db`
- `app.core.dependencies` — `get_current_user`
- `app.core.exceptions` — `AppException`
- No depende de ningún otro módulo del proyecto