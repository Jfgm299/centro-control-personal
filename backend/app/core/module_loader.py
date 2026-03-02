"""
Auto-discovery de módulos instalados en app/modules/.
Un módulo es válido si tiene manifest.py con SCHEMA_NAME.
"""
import pkgutil
import importlib
from pathlib import Path

_MODULES_PATH = Path(__file__).parent.parent / "modules"
_MODULES_PACKAGE = "app.modules"


def get_installed_modules() -> list[str]:
    """Devuelve los nombres de todos los módulos descubiertos en app/modules/."""
    modules = []
    for item in _MODULES_PATH.iterdir():
        if item.is_dir() and (item / "manifest.py").exists():
            modules.append(item.name)
    return sorted(modules)


def import_module(module_name: str):
    """Importa y devuelve el paquete principal de un módulo."""
    return importlib.import_module(f"{_MODULES_PACKAGE}.{module_name}")


def import_all_models():
    """
    Importa models.py de cada módulo para que SQLAlchemy
    registre todos los modelos en Base.metadata.
    """
    for module_name in get_installed_modules():
        try:
            importlib.import_module(f"{_MODULES_PACKAGE}.{module_name}.models")
        except ModuleNotFoundError:
            pass  # módulo sin modelos (ej: solo lógica)


def get_all_schemas() -> list[str]:
    """Devuelve los SCHEMA_NAME de todos los módulos instalados."""
    schemas = []
    for module_name in get_installed_modules():
        try:
            manifest = importlib.import_module(
                f"{_MODULES_PACKAGE}.{module_name}.manifest"
            )
            if hasattr(manifest, "SCHEMA_NAME"):
                schemas.append(manifest.SCHEMA_NAME)
        except ModuleNotFoundError:
            pass
    return schemas

"""
Auto-discovery de módulos instalados en app/modules/.
Un módulo es válido si tiene manifest.py con SCHEMA_NAME.
"""
import importlib
from pathlib import Path

_MODULES_PATH = Path(__file__).parent.parent / "modules"
_MODULES_PACKAGE = "app.modules"


def get_installed_modules() -> list[str]:
    modules = []
    for item in sorted(_MODULES_PATH.iterdir()):
        if item.is_dir() and (item / "manifest.py").exists():
            modules.append(item.name)
    return modules


def import_module(module_name: str):
    return importlib.import_module(f"{_MODULES_PACKAGE}.{module_name}")


def import_all_models():
    """
    Importa models.py de cada módulo para que SQLAlchemy
    registre todos los modelos en Base.metadata.
    """
    for module_name in get_installed_modules():
        try:
            importlib.import_module(f"{_MODULES_PACKAGE}.{module_name}.models")
        except ModuleNotFoundError:
            pass


def get_all_schemas() -> list[str]:
    schemas = []
    for module_name in get_installed_modules():
        try:
            manifest = importlib.import_module(
                f"{_MODULES_PACKAGE}.{module_name}.manifest"
            )
            if hasattr(manifest, "SCHEMA_NAME"):
                schemas.append(manifest.SCHEMA_NAME)
        except ModuleNotFoundError:
            pass
    return schemas


def register_user_relationships():
    """
    Registra dinámicamente en User las relaciones declaradas por cada módulo.
    Cada módulo puede definir USER_RELATIONSHIPS en su manifest.py.

    Formato esperado en manifest.py:
        USER_RELATIONSHIPS = [
            {
                "name": "diary_entries",          # atributo en User
                "target": "DiaryEntry",            # nombre del modelo SQLAlchemy
                "back_populates": "user",          # back_populates en el modelo hijo
                "cascade": "all, delete-orphan",   # opcional
                "uselist": True,                   # opcional, default True
            },
        ]
    """
    from app.core.auth.user import User

    for module_name in get_installed_modules():
        try:
            manifest = importlib.import_module(
                f"{_MODULES_PACKAGE}.{module_name}.manifest"
            )
        except ModuleNotFoundError:
            continue

        relationships = getattr(manifest, "USER_RELATIONSHIPS", [])
        for rel in relationships:
            attr_name = rel["name"]

            # Si User ya tiene el atributo (ej: segunda carga por hot-reload), saltar
            if hasattr(User, attr_name):
                continue

            kwargs = {
                "back_populates": rel["back_populates"],
                "cascade":        rel.get("cascade", "all, delete-orphan"),
                "uselist":        rel.get("uselist", True),
            }

            from sqlalchemy.orm import relationship as sa_relationship
            setattr(User, attr_name, sa_relationship(rel["target"], **kwargs))