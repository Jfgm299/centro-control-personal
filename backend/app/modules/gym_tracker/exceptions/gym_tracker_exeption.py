from app.core.exeptions import AppException
from ..enums import GymSetType

class WorkoutAlreadyEndedError(AppException):
    def __init__(self, workout_id: int):
        super().__init__(
            message=f"Workout {workout_id} is already ended",
            status_code=409
        )
        self.workout_id = workout_id

class WorkoutNotFoundError(AppException):
    def __init__(self, workout_id:int):
        super().__init__(
            message=f"Workout {workout_id} not found", 
            status_code= 404)
        self.workout_id = workout_id

class WorkoutAlreadyActiveError(AppException):
    def __init__(self, workout_id:int):
        super().__init__(
            message=f"There is already a workout going on {workout_id}. Terminate it before continue.",
            status_code=409
        )
        self.workout_id = workout_id

class ExerciseNotFoundError(AppException):
    def __init__(self, exercise_id:int):
        super().__init__(
            message=f"Exercise {exercise_id} not found", 
            status_code= 404)
        self.exercise_id = exercise_id

class ExerciseNotInWorkoutError(AppException):
    def __init__(self, exercise_id:int, workout_id:int):
        super().__init__(
            message=f"Exercise {exercise_id} does not belong to workout {workout_id}",
            status_code= 409
        )
        self.exercise_id = exercise_id
        self.workout_id = workout_id

class SetNotFoundError(AppException):
    def __init__(self, set_id:int):
        super().__init__(
            message=f"Set {set_id} not found", 
            status_code= 404)
        self.set_id = set_id

class SetNotInExerciseError(AppException):
    def __init__(self, set_id:int, exercise_id:int):
        super().__init__(
            message=f"Set {set_id} does not belong to exercise {exercise_id}",
            status_code= 409
        )
        self.exercise_id = exercise_id
        self.set_id = set_id

class SetTypeMismatchError(AppException):
    def __init__(self, exercise_id: int, expected_type: GymSetType):
        super().__init__(
            message=f"Exercise {exercise_id} expects sets of type {expected_type.value}",
            status_code=409
        )
        self.exercise_id = exercise_id
        self.expected_type = expected_type

class BodyMeasureNotFound(AppException):
    def __init__(self, measure_id:int):
        super().__init__(
            message=f"Body Measurement {measure_id} not found", 
            status_code= 404)
        self.measure_id = measure_id