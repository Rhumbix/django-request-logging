import logging
import re

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.termcolors import colorize

MAX_BODY_LENGTH = 50000  # log no more than 3k bytes of content
SETTING_NAMES = {
    'log_level': 'REQUEST_LOGGING_DATA_LOG_LEVEL',
    'colorize': 'REQUEST_LOGGING_DISABLE_COLORIZE'
}
request_logger = logging.getLogger('django.request')


class Logger:
    def log(self, level, msg):
        for line in str(msg).split('\n'):
            request_logger.log(level, line)

    def log_error(self, level, msg):
        self.log(level, msg)


class ColourLogger(Logger):
    def __init__(self, log_colour, log_error_colour):
        self.log_colour = log_colour
        self.log_error_colour = log_error_colour

    def log(self, level, msg):
        self._log(level, msg, self.log_colour)

    def log_error(self, level, msg):
        self._log(level, msg, self.log_error_colour)

    def _log(self, level, msg, colour):
        for line in str(msg).split('\n'):
            line = colorize(line, fg=colour)
            request_logger.log(level, line)


class LoggingMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log_level = getattr(settings, SETTING_NAMES['log_level'], logging.DEBUG)
        if self.log_level not in [logging.NOTSET, logging.DEBUG, logging.INFO,
                                  logging.WARNING, logging.ERROR, logging.CRITICAL]:
            raise ValueError("Unknown log level({}) in setting({})".format(self.log_level, SETTING_NAMES['log_level']))

        enable_colorize = getattr(settings, SETTING_NAMES['colorize'], True)
        if type(enable_colorize) is not bool:
            raise ValueError(
                "{} should be boolean. {} is not boolean.".format(SETTING_NAMES['colorize'], enable_colorize)
            )

        self.logger = ColourLogger("cyan", "magenta") if enable_colorize else Logger()

    def process_request(self, request):
        method_path = "{} {}".format(request.method, request.get_full_path())
        self.logger.log(logging.INFO, method_path)

        headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}

        if headers:
            self.logger.log(self.log_level, headers)
        if request.body:
            self.logger.log(self.log_level, self._chunked_to_max(request.body))

    def process_response(self, request, response):
        resp_log = "{} {} - {}".format(request.method, request.get_full_path(), response.status_code)

        is_content_type_matched = re.match('^application/json', response.get('Content-Type', ''), re.I)

        if response.status_code in range(400, 600):
            self.logger.log_error(logging.INFO, resp_log)

            if is_content_type_matched:
                self.logger.log_error(logging.ERROR, response._headers)
                self.logger.log_error(logging.ERROR, self._chunked_to_max(response.content))
        else:
            self.logger.log(logging.INFO, resp_log)

            if is_content_type_matched:
                self.logger.log(self.log_level, response._headers)
                self.logger.log(self.log_level, self._chunked_to_max(response.content))

        return response

    def _chunked_to_max(self, msg):
        if len(msg) > MAX_BODY_LENGTH:
            return "{0}\n...\n".format(msg[0:MAX_BODY_LENGTH])

        return msg
