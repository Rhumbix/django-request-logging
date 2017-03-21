import io
import unittest

import mock
from django.conf import settings
from django.test import RequestFactory

import request_logging
from request_logging.middleware import LoggingMiddleware, MAX_BODY_LENGTH

settings.configure()


@mock.patch.object(request_logging.middleware, "request_logger")
class LogTestCase(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = LoggingMiddleware()

    def test_does_not_error_with_binary_content_larger_than_chunk_size(self, mock_log):
        body = MAX_BODY_LENGTH * "0" + "1"
        datafile = io.StringIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile})
        self.middleware.process_request(request)
        self.assert_logged(mock_log, str(request.body[:MAX_BODY_LENGTH]))
        self.assert_not_logged(mock_log, body)

    def test_request_body_logged(self, mock_log):
        body = "some body"
        datafile = io.StringIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile})
        self.middleware.process_request(request)
        self.assert_logged(mock_log, "some body")

    def test_request_headers_logged(self, mock_log):
        request = self.factory.post("/somewhere",
                                    **{'HTTP_USER_AGENT': 'silly-human'})
        self.middleware.process_request(request)
        self.assert_logged(mock_log, "HTTP_USER_AGENT")

    def test_response_headers_logged(self, mock_log):
        request = self.factory.post("/somewhere")
        response = mock.MagicMock()
        response.get.return_value = 'application/json'
        response._headers = {'test_headers': 'test_headers'}
        self.middleware.process_response(request, response)
        self.assert_logged(mock_log, "test_headers")

    def assert_logged(self, mock_log, expected_entry):
        calls = mock_log.log.call_args_list
        text = " ".join([call[0][1] for call in calls])
        self.assertTrue(expected_entry in text)

    def assert_not_logged(self, mock_log, unexpected_entry):
        calls = mock_log.log.call_args_list
        text = " ".join([call[0][1] for call in calls])
        self.assertTrue(unexpected_entry not in text)
