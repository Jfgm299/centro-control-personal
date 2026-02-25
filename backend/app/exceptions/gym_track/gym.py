from ..base import AppException

class WorkoutAlreadyEndedError(AppException):
    def __init__(self, workout_id: int):
        super().__init__(
            message=f"Workout {workout_id} is already ended",
            status_code=409
        )
        self.workout_id = workout_id

class WorkoutNotFound(AppException):
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
