from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core import Base
from app.modules.expenses_tracker import expense
from app.modules.gym_tracker.models import *
from app.modules.flights_tracker.flight import Flight   # ← nuevo
from app.core.auth.user import User

# Añade estas 3 líneas junto a los otros imports de módulos:
from app.modules.macro_tracker.product import Product          # noqa: F401
from app.modules.macro_tracker.diary_entry import DiaryEntry   # noqa: F401
from app.modules.macro_tracker.user_goal import UserGoal       # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # ← Crear schemas antes de las migraciones
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS gym_tracker"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS expenses_tracker"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS flights_tracker"))  # ← nuevo
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS macro_tracker"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()