from .automation_handlers import AUTOMATION_EXCEPTION_HANDLERS
from app.core.handlers import CORE_EXCEPTION_HANDLERS


def register_exception_handlers(app):
    all_handlers = {**CORE_EXCEPTION_HANDLERS, **AUTOMATION_EXCEPTION_HANDLERS}
    for exc_class, handler in all_handlers.items():
        app.add_exception_handler(exc_class, handler)