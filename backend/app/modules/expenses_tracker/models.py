# app/modules/expenses_tracker/models.py
# Re-exporta todos los modelos para que alembic/env.py
# los encuentre con import_all_models()
from .expense import Expense  # noqa: F401