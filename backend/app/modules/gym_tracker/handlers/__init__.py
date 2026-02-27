from .gym_handlers import GYM_EXCEPTION_HANDLERS
from app.core.handlers import CORE_EXCEPTION_HANDLERS

def register_exception_handlers(app):
    """Registra todos los exception handlers de la aplicación"""
    # Primero core, luego los específicos de módulo
    all_handlers = {**CORE_EXCEPTION_HANDLERS, **GYM_EXCEPTION_HANDLERS}
    for exc_class, handler in all_handlers.items():
        app.add_exception_handler(exc_class, handler)