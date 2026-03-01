from .travel_handlers import TRAVELS_EXCEPTION_HANDLERS


def register_exception_handlers(app):
    for exc_class, handler in TRAVELS_EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exc_class, handler)