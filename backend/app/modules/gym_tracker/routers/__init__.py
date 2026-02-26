from .workouts_router import router as workouts_router
from .exercises_router import router as exercises_router
from .sets_router import router as sets_router
from .body_measurement_router import router as body_measurements_router

__all__ = [workouts_router,exercises_router, sets_router, body_measurements_router]