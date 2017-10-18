import logging
import re

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.termcolors import colorize

DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_COLORIZE = True
DEFAULT_MAX_BODY_LENGTH = 50000  # log no more than 3k bytes of content
SETTING_NAMES = {
    'log_level': 'REQUEST_LOGGING_DATA_LOG_LEVEL',
    'colorize': 'REQUEST_LOGGING_DISABLE_COLORIZE',
    'max_body_length': 'REQUEST_LOGGING_MAX_BODY_LENGTH'
}
BINARY_REGEX = re.compile('(.+Content-Type:.*?)(\S+)/(\S+)(?:\r\n)*(.+)', re.S | re.I)
BINARY_TYPES = ('image', 'application')
request_logger = logging.getLogger('django.request')


class Logger:
    def log(self, level, msg, extra=None):
        for line in str(msg).split('\n'):
            request_logger.log(level, line, extra=extra)

    def log_error(self, level, msg, extra=None):
        self.log(level, msg, extra=extra)


class ColourLogger(Logger):
    def __init__(self, log_colour, log_error_colour):
        self.log_colour = log_colour
        self.log_error_colour = log_error_colour

    def log(self, level, msg, extra=None):
        colour = self.log_error_colour if level >= logging.ERROR else self.log_colour
        self._log(level, msg, colour, extra=extra)

    def log_error(self, level, msg, extra=None):
        # Forces colour to be log_error_colour no matter what level is
        self._log(level, msg, self.log_error_colour, extra)

    def _log(self, level, msg, colour, extra=None):
        for line in str(msg).split('\n'):
            line = colorize(line, fg=colour)
            request_logger.log(level, line, extra=extra)


class LoggingMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        super(LoggingMiddleware, self).__init__(*args, **kwargs)

        self.log_level = getattr(settings, SETTING_NAMES['log_level'], DEFAULT_LOG_LEVEL)
        if self.log_level not in [logging.NOTSET, logging.DEBUG, logging.INFO,
                                  logging.WARNING, logging.ERROR, logging.CRITICAL]:
            raise ValueError("Unknown log level({}) in setting({})".format(self.log_level, SETTING_NAMES['log_level']))

        enable_colorize = getattr(settings, SETTING_NAMES['colorize'], DEFAULT_COLORIZE)
        if type(enable_colorize) is not bool:
            raise ValueError(
                "{} should be boolean. {} is not boolean.".format(SETTING_NAMES['colorize'], enable_colorize)
            )

        self.max_body_length = getattr(settings, SETTING_NAMES['max_body_length'], DEFAULT_MAX_BODY_LENGTH)
        if type(self.max_body_length) is not int:
            raise ValueError(
                "{} should be int. {} is not int.".format(SETTING_NAMES['max_body_length'], self.max_body_length)
            )

        self.logger = ColourLogger("cyan", "magenta") if enable_colorize else Logger()
        self.boundary = ''

    def process_request(self, request):
        method_path = "{} {}".format(request.method, request.get_full_path())
        extra = self._get_log_record_extra(request, None)
        self.logger.log(logging.INFO, method_path, extra=extra)

        content_type = request.META.get('CONTENT_TYPE', '')
        is_multipart = content_type.startswith('multipart/form-data')
        if is_multipart:
            self.boundary = '--' + content_type[30:]  # First 30 characters are "multipart/form-data; boundary="

        headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}

        if headers:
            self.logger.log(self.log_level, headers, extra=extra)
        if request.body:
            if is_multipart:
                self._log_multipart(self._chunked_to_max(request.body))
            else:
                self.logger.log(self.log_level, self._chunked_to_max(request.body), extra=extra)

    def process_response(self, request, response):
        resp_log = "{} {} - {}".format(request.method, request.get_full_path(), response.status_code)
        extra = self._get_log_record_extra(request, response)

        if response.status_code in range(400, 600):
            self.logger.log_error(logging.INFO, resp_log, extra=extra)
            self._log_resp(logging.ERROR, response, extra=extra)
        else:
            self.logger.log(logging.INFO, resp_log, extra=extra)
            self._log_resp(self.log_level, response, extra=extra)

        return response

    def _get_log_record_extra(self, request, response):
        return {'request': request, 'response': response}

    def _log_multipart(self, body, extra=None):
        """
        Splits multipart body into parts separated by "boundary", then matches each part to BINARY_REGEX
        which searches for existance of "Content-Type" and capture of what type is this part.
        If it is an image or an application replace that content with "(binary data)" string.
        """
        parts = str(body).split(self.boundary)
        last = len(parts) - 1
        for i, part in enumerate(parts):
            if 'Content-Type:' in part:
                match = BINARY_REGEX.search(part)
                if match and match.group(2) in BINARY_TYPES and not match.group(4) in ('', '\r\n'):
                    part = match.expand(r'\1\2/\3\r\n\r\n(binary data)\r\n')

            if i != last:
                part = part + self.boundary

            self.logger.log(self.log_level, part, extra=extra)

    def _log_resp(self, level, response, extra=None):
        if re.match('^application/json', response.get('Content-Type', ''), re.I):
            self.logger.log(level, response._headers, extra=extra)
            self.logger.log(level, self._chunked_to_max(response.content), extra=extra)

    def _chunked_to_max(self, msg):
        return msg[0:self.max_body_length]

