# app/modules/gym_tracker/__init__.py
from fastapi import APIRouter


from .routers.workouts_router import router as workouts_router
from .routers.exercises_router import router as exercises_router
from .routers.sets_router import router as sets_router
from .routers.body_measurement_router import router as body_router

router = APIRouter()
router.include_router(workouts_router)
router.include_router(exercises_router)
router.include_router(sets_router)
router.include_router(body_router)


TAGS = [
    {"name": "Workouts",          "description": "Sesiones de entrenamiento"},
    {"name": "Exercises",         "description": "Ejercicios dentro de un entreno"},
    {"name": "Sets",              "description": "Series dentro de un ejercicio"},
    {"name": "Body Measurements", "description": "Medidas corporales"},
]

TAG_GROUP = {
    "name": "Gym Tracker",
    "tags": ["Workouts", "Exercises", "Sets", "Body Measurements"]
}

__all__ = ['router', 'TAGS', 'TAG_GROUP']