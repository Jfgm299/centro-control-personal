# 🥗 Macro Tracker

Módulo de registro y análisis de macronutrientes diarios. El usuario escanea el código de barras de un producto con la cámara del móvil (o lo busca por nombre / introduce el código manualmente en PC), el backend consulta Open Food Facts **una sola vez**, persiste el producto en caché local, y a partir de ese momento cualquier usuario puede usarlo sin llamadas adicionales a la API externa.

Inspirado en [MyFitnessPal](https://www.myfitnesspal.com/) / [Cronometer](https://cronometer.com/) — registro de comidas por comida del día con desglose de macros y seguimiento de objetivos personales.

---

## ¿Qué hace?

Permite registrar la ingesta nutricional diaria especificando producto + cantidad en gramos + comida del día. El sistema calcula automáticamente todos los macronutrientes para esa cantidad y los acumula en el diario del usuario. Incluye un resumen diario por comidas, seguimiento de objetivos y estadísticas de período.

---

## Instalación

Añade el módulo a `INSTALLED_MODULES` en tu configuración:

```python
# core/config.py
INSTALLED_MODULES = [
    "macro_tracker",
    # otros módulos...
]
```

Añade la variable de entorno:

```env
# .env
OFF_BASE_URL=https://world.openfoodfacts.org
```

Aplica la migración:

```bash
docker-compose exec api alembic upgrade head
```

Para desactivarlo, comenta o elimina la línea de `INSTALLED_MODULES`. El resto de módulos no se verá afectado.

---

## API externa — Open Food Facts

El módulo usa [Open Food Facts](https://world.openfoodfacts.org/data) como fuente de datos de productos.

| Característica | Detalle |
|----------------|---------|
| Precio | Gratuito, sin API key |
| Productos | 4M+ de 150 países |
| Rate limit | ~1000 req/día por IP sin problemas |
| Licencia | ODbL — permite cachear los datos |
| Autenticación | Ninguna (solo User-Agent identificativo) |

### Principio de mínimas llamadas

| Operación | Llamadas a OFF |
|-----------|----------------|
| `GET /macros/products/barcode/{barcode}` — producto nuevo | 1 |
| `GET /macros/products/barcode/{barcode}` — ya en caché | **0** |
| `GET /macros/products/search` — pocos resultados locales | 1 |
| `GET /macros/products/search` — suficientes resultados locales (≥5) | **0** |
| Todos los demás endpoints | **0** |

---

## Endpoints

Base URL: `/api/v1/macros`

### Productos

| Método | Ruta | Status | Descripción | API call |
|--------|------|--------|-------------|----------|
| `GET` | `/products/barcode/{barcode}` | 200 | Buscar por EAN/UPC. Cache-first. | ⚡ 0 ó 1 |
| `GET` | `/products/search?q=` | 200 | Buscar por nombre. Local-first. | ⚡ 0 ó 1 |
| `GET` | `/products/{product_id}` | 200 | Obtener producto del catálogo por ID | — |

### Diario

| Método | Ruta | Status | Descripción |
|--------|------|--------|-------------|
| `POST` | `/diary` | 201 | Añadir entrada. Calcula nutrientes automáticamente. |
| `GET` | `/diary` | 200 | Listar entradas con filtros opcionales de fecha y comida |
| `GET` | `/diary/summary?date=` | 200 | Resumen del día: por comida + totales + % objetivos |
| `PATCH` | `/diary/{entry_id}/amount` | 200 | Actualizar cantidad y recalcular nutrientes |
| `PATCH` | `/diary/{entry_id}/notes` | 200 | Actualizar notas personales |
| `DELETE` | `/diary/{entry_id}` | 204 | Eliminar entrada |

### Objetivos y estadísticas

| Método | Ruta | Status | Descripción |
|--------|------|--------|-------------|
| `GET` | `/goals` | 200 | Obtener objetivos del usuario. Los crea con defaults si no existen. |
| `PUT` | `/goals` | 200 | Crear o actualizar objetivos (campos opcionales) |
| `GET` | `/stats?days=30` | 200 | Estadísticas del período: medias, consistencia, top productos |

> ⚠️ **Orden crítico de rutas**: `/products/barcode/{barcode}`, `/products/search`, `/diary/summary`, `/stats` y `/goals` están declaradas antes de las rutas con parámetros (`/products/{product_id}`, `/diary/{entry_id}/...`) para evitar que FastAPI interprete rutas literales como parámetros.

---

## Modelos

### Product — catálogo global

La tabla `macro_tracker.products` es compartida por todos los usuarios. Cuando un usuario escanea un barcode nuevo, el producto queda disponible para todos. Nadie puede borrar productos del catálogo (solo sus propias entradas del diario).

| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| `id` | `int` | — | PK autoincremental |
| `barcode` | `str(30)` | ✓ | EAN-13 o UPC-A. UNIQUE (partial index, excluye NULL) |
| `product_name` | `str(200)` | — | Nombre del producto |
| `brand` | `str(100)` | ✓ | Marca (primera si OFF devuelve varias) |
| `serving_size_text` | `str(50)` | ✓ | Texto de la porción ("100g", "1 vaso") |
| `serving_quantity_g` | `float` | ✓ | Gramos de la porción estándar |
| `nutriscore` | `str(1)` | ✓ | Nutri-Score: a, b, c, d, e |
| `image_url` | `str(500)` | ✓ | URL de la foto del producto |
| `categories` | `str(500)` | ✓ | Tags de categoría de OFF |
| `allergens` | `str(300)` | ✓ | Tags de alérgenos de OFF |
| `energy_kcal_100g` | `float` | ✓ | Calorías por 100g |
| `proteins_100g` | `float` | ✓ | Proteínas por 100g (g) |
| `carbohydrates_100g` | `float` | ✓ | Carbohidratos por 100g (g) |
| `sugars_100g` | `float` | ✓ | Azúcares por 100g (g) |
| `fat_100g` | `float` | ✓ | Grasas por 100g (g) |
| `saturated_fat_100g` | `float` | ✓ | Grasas saturadas por 100g (g) |
| `fiber_100g` | `float` | ✓ | Fibra por 100g (g) |
| `salt_100g` | `float` | ✓ | Sal por 100g (g) |
| `sodium_100g` | `float` | ✓ | Sodio por 100g (g) |
| `source` | `str(20)` | — | Origen del dato (openfoodfacts / manual) |
| `off_raw_data` | `JSON` | ✓ | Respuesta raw cacheada de OFF |
| `created_at` | `datetime(TZ)` | — | server_default=now() |
| `updated_at` | `datetime(TZ)` | ✓ | onupdate=now() |

> ⚠️ **Todos los nutrientes son opcionales en OFF.** Muchos productos solo tienen calorías y macros básicos. El cliente usa `.get()` defensivo en todos los campos de `nutriments`.

### DiaryEntry — diario personal

| Campo | Tipo | Nullable | Descripción |
|-------|------|----------|-------------|
| `id` | `int` | — | PK autoincremental |
| `user_id` | `int` | — | FK a `core.users.id` (CASCADE DELETE) |
| `product_id` | `int` | — | FK a `macro_tracker.products.id` |
| `entry_date` | `date` | — | Fecha de la toma (hora local del usuario) |
| `meal_type` | `MealType` | — | Comida del día |
| `amount_g` | `float` | — | Cantidad consumida en gramos |
| `energy_kcal` | `float` | ✓ | Calculado: `energy_kcal_100g × amount_g / 100` |
| `proteins_g` | `float` | ✓ | Calculado para `amount_g` |
| `carbohydrates_g` | `float` | ✓ | Calculado para `amount_g` |
| `sugars_g` | `float` | ✓ | Calculado para `amount_g` |
| `fat_g` | `float` | ✓ | Calculado para `amount_g` |
| `saturated_fat_g` | `float` | ✓ | Calculado para `amount_g` |
| `fiber_g` | `float` | ✓ | Calculado para `amount_g` |
| `salt_g` | `float` | ✓ | Calculado para `amount_g` |
| `notes` | `text` | ✓ | Notas personales del usuario |
| `created_at` | `datetime(TZ)` | — | server_default=now() |
| `updated_at` | `datetime(TZ)` | ✓ | onupdate=now() |

### MealType (enum)

| Valor | Descripción |
|-------|-------------|
| `breakfast` | Desayuno |
| `morning_snack` | Media mañana |
| `lunch` | Comida |
| `afternoon_snack` | Merienda |
| `dinner` | Cena |
| `other` | Otro (snack nocturno, etc.) |

### UserGoal — objetivos por usuario

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `id` | `int` | — | PK autoincremental |
| `user_id` | `int` | — | FK a `core.users.id`. UNIQUE (un goal por usuario). |
| `energy_kcal` | `float` | 2000.0 | Objetivo calórico diario |
| `proteins_g` | `float` | 150.0 | Objetivo de proteínas (g) |
| `carbohydrates_g` | `float` | 250.0 | Objetivo de carbohidratos (g) |
| `fat_g` | `float` | 65.0 | Objetivo de grasas (g) |
| `fiber_g` | `float` | 25.0 | Objetivo de fibra (g) |

Los objetivos se crean automáticamente con estos defaults en el primer acceso. El usuario nunca recibe 404 en `/goals`.

---

## Schemas Pydantic

### DiaryEntryCreate — input del usuario

| Campo | Tipo | Validación |
|-------|------|------------|
| `product_id` | `int` | ID del producto ya en catálogo |
| `entry_date` | `date` | Fecha de la toma |
| `meal_type` | `MealType` | Enum de comida |
| `amount_g` | `float` | `gt=0`, `le=5000`. Se redondea a 1 decimal. |
| `notes` | `str \| None` | Opcional |

### DailySummaryResponse — resumen del día

| Campo | Descripción |
|-------|-------------|
| `date` | Fecha del resumen |
| `meals` | Lista de `MealSummary` (solo comidas con entradas, en orden lógico) |
| `totals` | `NutrientTotals` — suma de todos los nutrientes del día |
| `goals` | `UserGoalResponse` — objetivos del usuario |
| `progress` | `GoalProgress` — % de objetivo alcanzado (energy, proteins, carbs, fat) |

### StatsResponse — estadísticas del período

| Campo | Descripción |
|-------|-------------|
| `period_days` | Días del período solicitado (parámetro `days`) |
| `days_logged` | Días con al menos 1 entrada |
| `total_entries` | Total de entradas en el período |
| `consistency_pct` | `days_logged / period_days × 100` |
| `daily_average` | `DailyAverage` — medias por nutriente divididas por `days_logged`, no por `period_days` |
| `top_products` | Top 10 productos por frecuencia de uso |

---

## Escaner de código de barras (frontend)

El backend recibe el barcode como string. La captura es responsabilidad exclusiva del frontend.

### Móvil

```javascript
// Detección automática del mejor método disponible
async function createBarcodeScanner() {
  if ('BarcodeDetector' in window) {
    const supported = await BarcodeDetector.getSupportedFormats();
    if (supported.includes('ean_13')) return new NativeBarcodeScanner(); // Chrome/Android
  }
  return new ZxingBarcodeScanner(); // Fallback: Firefox/Safari/iOS
}
```

| Navegador | API nativa | @zxing/browser |
|-----------|------------|----------------|
| Chrome 83+ / Android | ✅ hardware-accel | ✅ |
| Edge 83+ | ✅ | ✅ |
| Firefox | ❌ | ✅ |
| Safari / iOS 15+ | ❌ | ✅ |

### PC / Desktop

En PC no tiene sentido el escáner en vivo. Se ofrecen dos alternativas:

```jsx
function PCBarcodeInput({ onScan, onSearchByName }) {
  // Opción 1: subir foto → detectar barcode desde imagen
  // Opción 2: escribir el EAN manualmente (cómodo con teclado)
  // Opción 3: buscar por nombre del producto
}
```

> El atributo `capture="environment"` en `<input type="file">` solo tiene efecto en móvil. En PC se ignora y abre el explorador de archivos, que es exactamente lo que se quiere.

```javascript
const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
// isMobile → LiveBarcodeScanner (cámara en vivo)
// !isMobile → PCBarcodeInput (archivo + texto manual)
```

---

## Ejemplos de uso

### Buscar producto por barcode

```http
GET /api/v1/macros/products/barcode/8480000342591
Authorization: Bearer <token>
```

```json
{
  "id": 1,
  "barcode": "8480000342591",
  "product_name": "Arroz redondo",
  "brand": "Hacendado",
  "nutriscore": "b",
  "energy_kcal_100g": 354.0,
  "proteins_100g": 7.0,
  "carbohydrates_100g": 77.0,
  "fat_100g": 0.9,
  "fiber_100g": 0.6,
  "source": "openfoodfacts"
}
```

### Añadir entrada al diario

```http
POST /api/v1/macros/diary
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_id": 1,
  "entry_date": "2026-03-01",
  "meal_type": "lunch",
  "amount_g": 150
}
```

```json
{
  "id": 1,
  "product_id": 1,
  "entry_date": "2026-03-01",
  "meal_type": "lunch",
  "amount_g": 150.0,
  "energy_kcal": 531.0,
  "proteins_g": 10.5,
  "carbohydrates_g": 115.5,
  "fat_g": 1.35,
  "product": { "id": 1, "product_name": "Arroz redondo", "..." }
}
```

### Resumen del día

```http
GET /api/v1/macros/diary/summary?date=2026-03-01
Authorization: Bearer <token>
```

### Actualizar objetivos

```http
PUT /api/v1/macros/goals
Authorization: Bearer <token>
Content-Type: application/json

{
  "energy_kcal": 2500.0,
  "proteins_g": 180.0
}
```

Los campos no enviados se conservan (partial update).

### Estadísticas de los últimos 30 días

```http
GET /api/v1/macros/stats?days=30
Authorization: Bearer <token>
```

---

## Autenticación y ownership

Todos los endpoints requieren JWT válido (`Authorization: Bearer <token>`). Sin token → **401**.

**DiaryEntry y UserGoal** son personales: se filtran siempre por `user_id == user.id`. Si la entrada no existe o pertenece a otro usuario → **404**. Nunca se devuelve 403 para no revelar si un recurso existe.

**Product** es global: cualquier usuario puede escanear un nuevo barcode y queda disponible para todos. Un usuario no puede borrar productos del catálogo, solo sus propias entradas del diario.

---

## Errores

| Excepción | HTTP | Cuándo ocurre |
|-----------|------|---------------|
| `ProductNotFoundInAPIError` | 404 | Barcode no existe en Open Food Facts |
| `ProductNotFoundError` | 404 | `product_id` no existe en el catálogo local |
| `DiaryEntryNotFoundError` | 404 | `entry_id` no existe o no pertenece al usuario |
| `OFFTimeoutError` | 503 | OFF no responde en 10 segundos |
| `OFFRateLimitError` | 503 | Rate limit de OFF (HTTP 429) |
| `OFFError` | 503 | Error genérico de OFF (5xx) |

---

## Estructura del módulo

```
macro_tracker/
├── __init__.py                    # Exporta router, TAGS, TAG_GROUP
├── product.py                     # Modelo SQLAlchemy — catálogo global
├── diary_entry.py                 # Modelo SQLAlchemy — diario personal
├── user_goal.py                   # Modelo SQLAlchemy — objetivos por usuario
├── macro_schema.py                # Schemas Pydantic (todos los inputs y outputs)
├── macro_router.py                # Endpoints FastAPI (orden crítico de rutas)
├── openfoodfacts_client.py        # Cliente HTTP async para Open Food Facts
├── enums/
│   └── meal_type.py               # MealType enum
├── exceptions/
│   └── macro_exceptions.py        # 6 excepciones específicas del módulo
├── handlers/
│   └── macro_handlers.py          # Exception handlers → JSONResponse
├── services/
│   ├── food_service.py            # Lógica de productos y caché
│   ├── diary_service.py           # Lógica de entradas diarias y objetivos
│   └── stats_service.py           # Estadísticas (Python puro, sin DB)
└── tests/
    ├── test_products.py           # 19 tests de productos y barcode
    ├── test_diary.py              # 36 tests de diario, summary y objetivos
    ├── test_stats.py              # 8 tests de estadísticas
    └── test_off_client.py         # 12 tests del cliente OFF
```

---

## Tests

```bash
# Solo este módulo
docker-compose exec api pytest app/modules/macro_tracker/tests/ -v

# Todos los tests del proyecto
docker-compose exec api pytest
```

### Cobertura — 75 tests nuevos

| Clase | Tests |
|-------|-------|
| `TestProductsAuth` | 5 |
| `TestBarcodeSearch` | 12 |
| `TestProductSearch` | 4 |
| `TestDiaryAuth` | 3 |
| `TestDiaryOwnership` | 3 |
| `TestAddDiaryEntry` | 9 |
| `TestUpdateDiaryEntry` | 5 |
| `TestDeleteDiaryEntry` | 4 |
| `TestDailySummary` | 4 |
| `TestGoals` | 5 |
| `TestStats` | 8 |
| `TestParseProduct` | 8 |
| `TestGetProduct` | 4 |
| **Total** | **74** |

> CERO llamadas reales a Open Food Facts en los tests — todo mockeado con `AsyncMock`. Los fixtures `mock_off_client`, `mock_off_not_found`, `mock_off_timeout`, `mock_off_rate_limit` y `mock_off_partial` parchean `OpenFoodFactsClient.get_product` con datos estáticos.

---

## Dependencias

- `httpx>=0.25.2` — cliente HTTP async para llamadas a Open Food Facts (ya presente si tienes `flights_tracker`)
- `pytest-asyncio` — soporte para tests async (`asyncio_mode = auto` en `pytest.ini`)
- `app.core.database` — `Base`, `get_db`
- `app.core.dependencies` — `get_current_user`
- `app.core.exeptions` — `AppException`
- No depende de ningún otro módulo del proyecto