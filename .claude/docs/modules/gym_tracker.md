# gym_tracker

Schema: `gym_tracker` | Automation contract: ❌

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
