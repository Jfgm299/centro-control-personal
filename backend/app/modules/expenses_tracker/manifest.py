SCHEMA_NAME = "expenses_tracker"

# Sin settings propios — no usa API externa
# Sin USER_RELATIONSHIPS declaradas aquí porque Expense ya tenía
# su relación definida directamente en user.py antes de la refactorización.
# Añádela aquí y elimínala de user.py:
USER_RELATIONSHIPS = [
    {
        "name": "expenses",
        "target": "Expense",
        "back_populates": "user",
        "cascade": "all, delete-orphan",
    },
]