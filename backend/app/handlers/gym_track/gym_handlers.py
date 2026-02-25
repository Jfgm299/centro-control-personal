from fastapi import Request
from fastapi.responses import JSONResponse
from ...exceptions import WorkoutAlreadyEndedError, WorkoutNotFoundError, WorkoutAlreadyActiveError, ExerciseNotFoundError, ExerciseNotInWorkoutError, SetNotInExerciseError, SetNotFoundError, SetTypeMismatchError, BodyMeasureNotFound

async def workout_already_ended_handler(request: Request, exc: WorkoutAlreadyEndedError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )

async def workout_not_found_handler(request: Request, exc: WorkoutNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.message}
    )

async def workout_already_active_handler(request: Request, exc: WorkoutAlreadyActiveError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.message}
    )

async def exercise_not_found_handler(request: Request, exc: ExerciseNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail":exc.message}
    )

async def exercise_not_in_workout_handler(request: Request, exc: ExerciseNotInWorkoutError):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail':exc.message}
    )

async def set_not_found_handler(request: Request, exc: SetNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail':exc.message}
    )

async def set_not_in_exercise_handler(request: Request, exc: SetNotInExerciseError):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail':exc.message}
    )

async def set_type_mismatch_handler(request: Request, exc: SetTypeMismatchError):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail':exc.message}
    )

async def body_measurement_not_found_handler(request: Request, exc: BodyMeasureNotFound):
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail':exc.message}
    )



#Dicctionary to help register
GYM_EXCEPTION_HANDLERS = {
    WorkoutAlreadyEndedError: workout_already_ended_handler,
    WorkoutNotFoundError: workout_not_found_handler,
    WorkoutAlreadyActiveError: workout_already_active_handler,
    ExerciseNotFoundError: exercise_not_found_handler,
    ExerciseNotInWorkoutError: exercise_not_in_workout_handler,
    SetNotFoundError: set_not_found_handler,
    SetTypeMismatchError: set_type_mismatch_handler,
    BodyMeasureNotFound: body_measurement_not_found_handler
}