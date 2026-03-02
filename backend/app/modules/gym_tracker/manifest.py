SCHEMA_NAME = "gym_tracker"

USER_RELATIONSHIPS = [
    {
        "name": "workouts",
        "target": "Workout",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
    {
        "name": "body_measurements",
        "target": "BodyMeasurement",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]