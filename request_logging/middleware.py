import logging
import re
from django.utils.termcolors import colorize

request_logger = logging.getLogger('django.request')


class LoggingMiddleware(object):

    def process_request(self, request):
        request_logger.info(colorize("{} {}".format(request.method, request.get_full_path()), fg="cyan"))

    def process_response(self, request, response):
        if (response.status_code in range(400, 600)):
            self.log_req_body(request, level=logging.ERROR)
            self.log_resp_body(response, level=logging.ERROR)
        else:
            self.log_req_body(request)
            self.log_resp_body(response)

        msg = "{} {} - {}".format(request.method, request.get_full_path(), response.status_code)
        request_logger.info(colorize(msg, fg="cyan"))
        return response

    def log_req_body(self, request, level=logging.DEBUG):
        if (not request.body):
            return

        msg = "<<<<<<\n" + request.body
        self.log_body(msg, level)

    def log_resp_body(self, response, level=logging.DEBUG):
        if (not re.match('^application', response['Content-Type'], re.I)):  # only log content type: 'application/xxx'
            return

        msg = ">>>>>>\n" + response.content[0:100000]  # log no more than 100k bytes of content
        self.log_body(msg, level)

    def log_body(self, msg, level):
        for line in msg.split('\n'):
            line = colorize(line, fg="magenta") if (level >= logging.ERROR) else line
            request_logger.log(level, line)
