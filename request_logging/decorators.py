from functools import wraps
from .middleware import NO_LOGGING_ATTR, NO_LOGGING_MSG


def no_logging(msg=None):
    def wrapper(func):
        setattr(func, NO_LOGGING_ATTR, msg if msg else NO_LOGGING_MSG)
        return func
    return wrapper
