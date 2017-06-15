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


class LoggingMiddleware(MiddlewareMixin):
    def __init__(self):
        super().__init__()

        self.log_level = getattr(settings, SETTING_NAMES['log_level'], logging.DEBUG)
        if self.log_level not in [logging.NOTSET, logging.DEBUG, logging.INFO,
                                  logging.WARNING, logging.ERROR, logging.CRITICAL]:
            raise ValueError("Unknown log level({}) in setting({})".format(self.log_level, SETTING_NAMES['log_level']))

        self.enable_colorize = getattr(settings, SETTING_NAMES['colorize'], True)
        if type(self.enable_colorize) is not bool:
            raise ValueError(
                "{} should be boolean. {} is not boolean.".format(SETTING_NAMES['colorize'], self.enable_colorize)
            )

    def process_request(self, request):
        method_path = "{} {}".format(request.method, request.get_full_path())
        if self.enable_colorize:
            method_path = colorize(method_path, fg="cyan")
        request_logger.info(method_path)

        headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}
        if headers:
            self._log(headers)
        if request.body:
            self._log(self._chunked_to_max(request.body))

    def process_response(self, request, response):
        resp_log = "{} {} - {}".format(request.method, request.get_full_path(), response.status_code)
        if response.status_code in range(400, 600):
            if self.enable_colorize:
                resp_log = colorize(resp_log, fg="magenta")
            request_logger.info(resp_log)
            self._log_resp(response, level=logging.ERROR)
        else:
            if self.enable_colorize:
                resp_log = colorize(resp_log, fg="cyan")
            request_logger.info(resp_log)
            self._log_resp(response)

        return response

    def _log_resp(self, response, level=None):
        if not re.match('^application/json', response.get('Content-Type', ''), re.I):  # only log content type: 'application/xxx'
            return

        self._log(response._headers, level)
        self._log(self._chunked_to_max(response.content), level)

    def _log(self, msg, level=None):
        level = level if level else self.log_level
        for line in str(msg).split('\n'):
            if self.enable_colorize:
                line = colorize(line, fg="magenta") if (level >= logging.ERROR) else colorize(line, fg="cyan")
            request_logger.log(level, line)

    def _chunked_to_max(self, msg):
        if len(msg) > MAX_BODY_LENGTH:
            return "{0}\n...\n".format(msg[0:MAX_BODY_LENGTH])
        else:
            return msg
