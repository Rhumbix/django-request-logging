from functools import wraps
from .middleware import (
    NO_LOGGING_FUNCS,
    OPT_INTO_LOGGING_FUNCS,
    NO_LOGGING_MSG,
    NoLogging,
)


class DjangoRequestsCollidingDecorators(Exception):
    pass


def no_logging(msg=None, silent=False): # type: (str, bool) -> Callable[..., Any]
    def wrapper(func): # type: Callable[..., Any]
        no_logging_message = msg if msg else NO_LOGGING_MSG
        NO_LOGGING_FUNCS[func] = NoLogging(message=no_logging_message, silent=silent)

        if func in OPT_INTO_LOGGING_FUNCS:
            raise DjangoRequestsCollidingDecorators

        return func

    return wrapper


def opt_into_logging(func):  # type: (Callable[..., Any]) -> Callable[..., Any]
    # No need to ensure decorators do not collide, it happens within each
    # conditional annotation method
    OPT_INTO_LOGGING_FUNCS.add(func)
    if func in NO_LOGGING_FUNCS:
        raise DjangoRequestsCollidingDecorators

    return func
