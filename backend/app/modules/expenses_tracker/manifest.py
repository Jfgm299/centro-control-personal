SCHEMA_NAME = "expenses_tracker"

USER_RELATIONSHIPS = [
    {
        "name": "expenses",
        "target": "Expense",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
    {
        "name": "scheduled_expenses",
        "target": "ScheduledExpense",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]