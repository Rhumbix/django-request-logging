from .middleware import NO_LOGGING_ATTR, NO_LOGGING_MSG_ATTR, NO_LOGGING_MSG


def no_logging(msg=None, silent=False):
    def wrapper(func):
        setattr(func, NO_LOGGING_ATTR, True)
        setattr(func, NO_LOGGING_MSG_ATTR, (msg if msg else NO_LOGGING_MSG) if not silent else None)
        return func

    return wrapper
