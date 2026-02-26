# 🏋️ Gym Tracker

Módulo de seguimiento de entrenos, ejercicios y series.

## ¿Qué hace?

Permite registrar sesiones de entrenamiento completas con sus ejercicios y series. Soporta dos tipos de ejercicio: **fuerza** (peso + repeticiones) y **cardio** (velocidad + duración). Calcula automáticamente la duración del entreno y el número total de ejercicios y series al finalizarlo.

## Instalación

Añade el módulo a `INSTALLED_MODULES` en tu configuración:

```python
# core/config.py
INSTALLED_MODULES = [
    "gym_tracker",
    # otros módulos...
]
```

Para desactivarlo, comenta o elimina la línea. El resto de módulos no se verá afectado.

## Endpoints

Base URL: `/api/v1`

### Workouts

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/workouts/` | Listar todos los entrenos |
| `POST` | `/workouts/` | Iniciar un nuevo entreno |
| `GET` | `/workouts/{workout_id}` | Obtener un entreno |
| `GET` | `/workouts/{workout_id}/long` | Obtener un entreno con detalle completo |
| `POST` | `/workouts/{workout_id}` | Finalizar un entreno |
| `DELETE` | `/workouts/{workout_id}` | Eliminar un entreno |

### Exercises

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/workouts/{workout_id}/exercises` | Añadir ejercicio a un entreno |
| `GET` | `/workouts/{workout_id}/exercises` | Listar ejercicios de un entreno |
| `GET` | `/workouts/{workout_id}/{exercise_id}` | Obtener un ejercicio |
| `GET` | `/workouts/{workout_id}/{exercise_id}/long` | Obtener ejercicio con sus series |
| `DELETE` | `/workouts/{workout_id}/{exercise_id}` | Eliminar un ejercicio |

### Sets

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/workouts/{workout_id}/{exercise_id}/sets` | Añadir serie a un ejercicio |
| `GET` | `/workouts/{workout_id}/{exercise_id}/sets` | Listar series de un ejercicio |
| `DELETE` | `/workouts/{workout_id}/{exercise_id}/sets/{set_id}` | Eliminar una serie |

### Body Measurements

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/body-measures/` | Listar mediciones |
| `POST` | `/body-measures/` | Registrar medición |
| `GET` | `/body-measures/{measurement_id}` | Obtener una medición |
| `DELETE` | `/body-measures/{measurement_id}` | Eliminar una medición |

## Modelos

### Workout

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `int` | Identificador único |
| `muscle_groups` | `MuscleGroupCategory[]` | Grupos musculares trabajados |
| `started_at` | `datetime` | Inicio automático al crear |
| `ended_at` | `datetime` | Fin al llamar al endpoint de finalizar |
| `duration_minutes` | `int` | Calculado automáticamente al finalizar |
| `total_exercises` | `int` | Calculado automáticamente al finalizar |
| `total_sets` | `int` | Calculado automáticamente al finalizar |
| `notes` | `str` | Notas opcionales |

### Exercise

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `int` | Identificador único |
| `workout_id` | `int` | Entreno al que pertenece |
| `name` | `str` | Nombre del ejercicio |
| `exercise_type` | `GymSetType` | `Weight_reps` o `Cardio` |
| `order` | `int` | Posición en el entreno (auto-incremental) |
| `notes` | `str` | Notas opcionales |

### Set

El tipo de campos requeridos depende del `exercise_type` del ejercicio padre.

| Campo | Tipo | Weight_reps | Cardio |
|-------|------|-------------|--------|
| `weight_kg` | `float` | ✅ requerido | — |
| `reps` | `int` | ✅ requerido | — |
| `speed_kmh` | `float` | — | ✅ requerido |
| `duration_seconds` | `int` | — | ✅ requerido |
| `incline_percent` | `float` | — | opcional |
| `rpe` | `int` | opcional (1-10) | opcional (1-10) |
| `notes` | `str` | opcional | opcional |

> Si intentas crear una serie con campos incompatibles con el tipo del ejercicio, recibirás un error `409 SetTypeMismatchError`.

### MuscleGroupCategory (enum)

```
Chest · Back · Biceps · Triceps · Core · Abs · Shoulders · Legs
```

### GymSetType (enum)

```
Weight_reps · Cardio
```

## Ejemplos de uso

### Flujo completo de un entreno

**1. Iniciar entreno**
```http
POST /api/v1/workouts/
Content-Type: application/json

{
  "muscle_groups": ["Chest", "Triceps"],
  "notes": "Entreno de empuje"
}
```

**2. Añadir ejercicio de fuerza**
```http
POST /api/v1/workouts/1/exercises
Content-Type: application/json

{
  "name": "Press Banca",
  "exercise_type": "Weight_reps",
  "notes": "Agarre medio"
}
```

**3. Añadir serie**
```http
POST /api/v1/workouts/1/1/sets
Content-Type: application/json

{
  "weight_kg": 80.0,
  "reps": 10,
  "rpe": 7
}
```

**4. Finalizar entreno**
```http
POST /api/v1/workouts/1
Content-Type: application/json

{
  "notes": "Buena sesión"
}
```

### Ejercicio de cardio

```http
POST /api/v1/workouts/1/exercises
Content-Type: application/json

{
  "name": "Cinta",
  "exercise_type": "Cardio"
}
```

```http
POST /api/v1/workouts/1/2/sets
Content-Type: application/json

{
  "speed_kmh": 10.0,
  "incline_percent": 2.0,
  "duration_seconds": 1800,
  "rpe": 6
}
```

## Reglas de negocio

- Solo puede haber **un entreno activo** a la vez. Hay que finalizarlo antes de crear otro.
- Los ejercicios solo pueden añadirse a entrenos **no finalizados**.
- El `set_number` se incrementa automáticamente por ejercicio.
- El tipo de serie debe ser compatible con el `exercise_type` del ejercicio.
- Al eliminar un ejercicio, se eliminan en cascada todas sus series.
- Al eliminar un entreno, se eliminan en cascada todos sus ejercicios y series.

## Estructura del módulo

```
gym_tracker/
    __init__.py             # Exporta router combinado
    enums.py                # GymSetType, MuscleGroupCategory
    exceptions.py           # WorkoutNotFoundError, SetTypeMismatchError, etc.
    handlers/
        gym_handlers.py     # Registro de exception handlers
    models/
        __init__.py
        workout.py
        workout_muscle_group.py
        exercise.py
        set.py
        body_measurement.py
    schemas/
        __init__.py
        workout.py
        exercise.py
        set.py
        body_measurements.py
    services/
        __init__.py
        workout_service.py
        exercise_service.py
        set_service.py
        body_measurement_service.py
    routers/
        workouts_router.py
        exercises_router.py
        sets_router.py
        body_measurement_router.py
    tests/
        __init__.py
        test_workouts.py
        test_exercises.py
        test_sets.py
```

## Tests

```bash
# Ejecutar solo los tests de este módulo
docker-compose exec api pytest app/modules/gym_tracker/tests/ -v

# Ejecutar solo los tests de sets
docker-compose exec api pytest app/modules/gym_tracker/tests/test_sets.py -v
```

## Excepciones

| Excepción | Status | Cuándo |
|-----------|--------|--------|
| `WorkoutNotFoundError` | 404 | Workout no existe |
| `WorkoutAlreadyEndedError` | 409 | Workout ya finalizado |
| `WorkoutAlreadyActiveError` | 409 | Ya hay un workout activo |
| `ExerciseNotFoundError` | 404 | Ejercicio no existe |
| `ExerciseNotInWorkoutError` | 409 | Ejercicio no pertenece al workout |
| `SetNotFoundError` | 404 | Serie no existe |
| `SetNotInExerciseError` | 409 | Serie no pertenece al ejercicio |
| `SetTypeMismatchError` | 409 | Datos de serie incompatibles con tipo de ejercicio |

## Dependencias

- No depende de ningún otro módulo
- Requiere: `app.core.database` (Base, get_db)
- Requiere: `app.core.exceptions` (AppException)