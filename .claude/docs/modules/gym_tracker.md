# gym_tracker

Schema: `gym_tracker` | Automation contract: ✅

Módulo de seguimiento de entrenamientos. Módulo de referencia — estructura más limpia y completa del proyecto. Usar como plantilla al crear módulos nuevos.

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `Workout` | `gym_tracker.workouts` | Sesión de entrenamiento (start/end) |
| `Exercise` | `gym_tracker.exercises` | Ejercicio dentro de un workout |
| `Set` | `gym_tracker.sets` | Serie dentro de un ejercicio |
| `WorkoutMuscleGroup` | `gym_tracker.workout_muscle_groups` | Grupos musculares (calculados al cerrar workout) |
| `BodyMeasurement` | `gym_tracker.body_measurements` | Mediciones corporales independientes |
| `ExerciseCatalog` | `gym_tracker.exercise_catalog` | Catálogo de ejercicios predefinidos |

## User Relationships

```python
user.workouts          # List[Workout]
user.body_measurements # List[BodyMeasurement]
```

## Key Business Rules

- Solo puede haber **un workout activo** por usuario (`ended_at == None`). Intentar crear otro lanza `WorkoutAlreadyActiveError`.
- Los **muscle groups** del workout se calculan automáticamente al llamar `end_workout()` — se agregan los grupos de todos los ejercicios.
- Los **sets** tienen tipos (`Weight_reps`, `Cardio`) y se valida que el tipo coincida con el del ejercicio (`SetTypeMismatchError`).

## Structure

```
gym_tracker/
├── manifest.py
├── models/          ← un archivo por modelo
├── models.py        ← re-exporta todos los modelos (import único)
├── schemas/         ← Create / Response / DetailResponse por entidad
├── services/        ← clase-based singletons
├── routers/         ← un router por entidad
├── exceptions/      ← todas heredan de AppException
├── handlers/        ← exception handlers + register_exception_handlers()
├── enums/
└── tests/
```

## Routers / Endpoints

- `GET/POST /workouts/` — listar / iniciar workout
- `GET /workouts/{id}` — detalle básico
- `GET /workouts/{id}/long` — detalle con ejercicios y series
- `POST /workouts/{id}` — cerrar workout
- `DELETE /workouts/{id}`
- `GET/POST /workouts/{id}/exercises` — ejercicios del workout
- `GET/PATCH/DELETE /workouts/{id}/exercises/{ex_id}`
- `GET/POST /workouts/{workout_id}/{ex_id}/sets`
- `GET/PATCH/DELETE /workouts/{workout_id}/{ex_id}/sets/{set_id}`
- `GET/POST /body-measures/`
- `GET/PATCH/DELETE /body-measures/{id}`
- `GET/POST /exercise-catalog/`

## External Dependencies

Ninguna — módulo completamente local.

## Automation Contract Implementation

### Triggers registrados

| trigger_ref | Cuándo dispara | Cómo se detecta |
|-------------|---------------|-----------------|
| `gym_tracker.workout_started` | Al iniciar un workout | Hook en `workout_service.start_workout()` post-commit |
| `gym_tracker.workout_ended` | Al terminar un workout | Hook en `workout_service.end_workout()` post-commit |
| `gym_tracker.personal_record_weight` | Cuando un set supera el máximo histórico para ese ejercicio | Hook en `set_service.create_set()`: captura `previous_max` ANTES del insert, compara DESPUÉS del commit |
| `gym_tracker.body_measurement_recorded` | Al registrar una medición corporal | Hook en `body_measurement_service.create_measure()` post-commit |
| `gym_tracker.workout_inactivity` | Cuando el usuario lleva N días sin entrenar | Job diario del scheduler (09:00 UTC); deduplicación por `(user_id, "YYYY-MM-DD")` |

### Acciones registradas

| action_ref | Qué hace |
|------------|----------|
| `gym_tracker.get_last_workout_summary` | Devuelve el último workout terminado (o uno específico por `workout_id`) |
| `gym_tracker.get_weekly_stats` | Estadísticas semana actual o anterior (`week_offset`) |
| `gym_tracker.get_exercise_progression` | Progresión por sesión de un ejercicio (case-insensitive, agrupado por workout) |
| `gym_tracker.get_body_measurement_trend` | N mediciones más recientes + `weight_delta_kg` |

### Scheduler

`scheduler_service.py` registra un job diario vía APScheduler, arrancado en `startup_event` desde `main.py`:

| Job | Frecuencia | Qué hace |
|-----|-----------|----------|
| `job_check_workout_inactivity` | Diaria (09:00 UTC) | Itera automations activas con `trigger_ref=gym_tracker.workout_inactivity`, llama `dispatcher.on_workout_inactivity_check()` por usuario distinto |

Deduplicación en memoria: `(user_id, "YYYY-MM-DD")` — una vez por día por usuario.

### Nota técnica: PR detection

`set_service.create_set()` hace un SELECT de `max(weight_kg)` ANTES de insertar el nuevo set — esto garantiza comparar el nuevo peso contra el histórico real, sin incluirse a sí mismo. Solo aplica a sets de tipo `Weight_reps` con `weight_kg > 0`.

### Tests

No llamar `job_check_workout_inactivity()` directamente en tests — usa `SessionLocal()` apuntando al DB de dev (5432). En su lugar, llamar `dispatcher.on_workout_inactivity_check(user_id, db)` con la sesión de test.

Ver implementación completa:
- `backend/app/modules/gym_tracker/automation_registry.py`
- `backend/app/modules/gym_tracker/automation_handlers.py`
- `backend/app/modules/gym_tracker/automation_dispatcher.py`
- `backend/app/modules/gym_tracker/scheduler_service.py`
