from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core import Base
from app.core.auth.user import User  # noqa: F401 — siempre presente
from app.core.module_loader import import_all_models, get_all_schemas

# Auto-importa todos los modelos de todos los módulos instalados
import_all_models()

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
        # Crea el schema core siempre
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS core"))
        # Crea automáticamente el schema de cada módulo instalado
        for schema in get_all_schemas():
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
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