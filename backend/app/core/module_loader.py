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