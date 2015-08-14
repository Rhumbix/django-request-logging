import logging

request_logger = logging.getLogger('django.request')

class LoggingMiddleware(object):

    def process_request(self, request):
        request_logger.log(logging.DEBUG, "GET: {}. POST: {}".format(request.GET, request.POST))
    def process_response(self, request, response):
        request_logger.log(logging.DEBUG, "GET: {}. POST: {}".format(request.GET, request.POST))
        return response
