import logging
import re
from django.utils.termcolors import colorize
from django.conf import settings

MAX_BODY_LENGTH = 50000  # log no more than 3k bytes of content
request_logger = logging.getLogger('django.request')


def match_ignored(path, ignored_paths):
    for ignored in ignored_paths:
        if path.startswith(ignored):
            return True
    return False

class LoggingMiddleware(object):
    def __init__(self):
        self.ignored_paths = settings.REQUEST_LOGGER_IGNORED_PATHS

    def process_request(self, request):
        if not match_ignored(request.get_full_path(), self.ignored_paths):
            request_logger.info(colorize("{} {}".format(request.method, request.get_full_path()), fg="cyan"))
            if (request.body):
                self.log_body(self.chunked_to_max(request.body), level=logging.INFO)

    def process_response(self, request, response):
        if match_ignored(request.get_full_path(), self.ignored_paths):
            return response
        resp_log = "{} {} - {}".format(request.method, request.get_full_path(), response.status_code)
        if (response.status_code in range(400, 600)):
            request_logger.info(colorize(resp_log, fg="magenta"))
            self.log_resp_body(response, level=logging.ERROR)
        else:
            request_logger.info(colorize(resp_log, fg="cyan"))
            self.log_resp_body(response, level=logging.INFO)

        return response

    def log_resp_body(self, response, level=logging.DEBUG):
        if (not re.match('^application/json', response.get('Content-Type', ''), re.I)):  # only log content type: 'application/xxx'
            return

        self.log_body(self.chunked_to_max(response.content), level)

    def log_body(self, msg, level=logging.DEBUG):
        for line in str(msg).split('\n'):
            line = colorize(line, fg="magenta") if (level >= logging.ERROR) else colorize(line, fg="cyan")
            request_logger.log(level, line)

    def chunked_to_max(self, msg):
        if (len(msg) > MAX_BODY_LENGTH):
            return "{0}\n...\n".format(msg[0:MAX_BODY_LENGTH])
        else:
            return msg
