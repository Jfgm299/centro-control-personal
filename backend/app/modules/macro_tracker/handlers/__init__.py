from .macro_handlers import MACRO_EXCEPTION_HANDLERS


def register_exception_handlers(app):
    for exc_class, handler in MACRO_EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)