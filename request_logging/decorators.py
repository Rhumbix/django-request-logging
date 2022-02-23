from .middleware import NO_LOGGING_ATTR, NO_LOGGING_MSG_ATTR, NO_LOGGING_MSG, NO_LOGGING_DEFAULT_VALUE, \
    LOG_HEADERS_ATTR, LOG_HEADERS_DEFAULT_VALUE, LOG_BODY_ATTR, LOG_BODY_DEFAULT_VALUE, LOG_RESPONSE_ATTR, \
    LOG_RESPONSE_DEFAULT_VALUE, NO_RESPONSE_LOGGING_MSG_ATTR, NO_RESPONSE_LOGGING_MSG, NO_HEADER_LOGGING_MSG_ATTR, \
    NO_HEADER_LOGGING_MSG, NO_BODY_LOGGING_MSG_ATTR, NO_BODY_LOGGING_MSG


def no_logging(msg=None, silent=False, value=None, log_headers=None, no_header_logging_msg=None, log_body=None,
               no_body_logging_msg=None, log_response=None, no_response_logging_msg=None):
    def _set_attr(func, attr_name, value, default_value=None):
        setattr(func, attr_name, value if value is not None else default_value)

    def _set_attr_msg(func, silent_value, msg_attr_name, message, default_message=None):
        setattr(func, msg_attr_name, (message if message else default_message) if not silent_value else None)

    def wrapper(func):
        _set_attr(func, NO_LOGGING_ATTR, value, NO_LOGGING_DEFAULT_VALUE)
        _set_attr_msg(func, silent, NO_LOGGING_MSG_ATTR, msg, NO_LOGGING_MSG)

        _set_attr(func, LOG_HEADERS_ATTR, log_headers, LOG_HEADERS_DEFAULT_VALUE)
        _set_attr_msg(func, silent, NO_HEADER_LOGGING_MSG_ATTR, no_header_logging_msg, NO_HEADER_LOGGING_MSG)

        _set_attr(func, LOG_BODY_ATTR, log_body, LOG_BODY_DEFAULT_VALUE)
        _set_attr_msg(func, silent, NO_BODY_LOGGING_MSG_ATTR, no_body_logging_msg, NO_BODY_LOGGING_MSG)

        _set_attr(func, LOG_RESPONSE_ATTR, log_response, LOG_RESPONSE_DEFAULT_VALUE)
        _set_attr_msg(func, silent, NO_RESPONSE_LOGGING_MSG_ATTR, no_response_logging_msg, NO_RESPONSE_LOGGING_MSG)
        return func

    return wrapper
