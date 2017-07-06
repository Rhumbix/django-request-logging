import io
import unittest

import logging
import mock
from django.conf import settings
from django.test import RequestFactory, override_settings

import request_logging
from request_logging.middleware import LoggingMiddleware, DEFAULT_LOG_LEVEL, DEFAULT_COLORIZE, DEFAULT_MAX_BODY_LENGTH

settings.configure()


class BaseLogTestCase(unittest.TestCase):
    def _assert_logged(self, mock_log, expected_entry):
        calls = mock_log.log.call_args_list
        text = " ".join([call[0][1] for call in calls])
        self.assertTrue(expected_entry in text)

    def _assert_logged_with_level(self, mock_log, level):
        calls = mock_log.log.call_args_list
        called_levels = set(call[0][0] for call in calls)
        self.assertTrue(level in called_levels, "{} not in {}".format(level, called_levels))

    def _assert_not_logged(self, mock_log, unexpected_entry):
        calls = mock_log.log.call_args_list
        text = " ".join([call[0][1] for call in calls])
        self.assertTrue(unexpected_entry not in text)


@mock.patch.object(request_logging.middleware, "request_logger")
class LogTestCase(BaseLogTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = LoggingMiddleware()

    def test_request_body_logged(self, mock_log):
        body = "some body"
        datafile = io.StringIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile})
        self.middleware.process_request(request)
        self._assert_logged(mock_log, "some body")

    def test_request_headers_logged(self, mock_log):
        request = self.factory.post("/somewhere",
                                    **{'HTTP_USER_AGENT': 'silly-human'})
        self.middleware.process_request(request)
        self._assert_logged(mock_log, "HTTP_USER_AGENT")

    def test_response_headers_logged(self, mock_log):
        request = self.factory.post("/somewhere")
        response = mock.MagicMock()
        response.get.return_value = 'application/json'
        response._headers = {'test_headers': 'test_headers'}
        self.middleware.process_response(request, response)
        self._assert_logged(mock_log, "test_headers")


class BaseLogSettingsTestCase(BaseLogTestCase):
    def setUp(self):
        body = "some body"
        datafile = io.StringIO(body)
        self.request = RequestFactory().post(
            "/somewhere",
            data={'file': datafile},
            **{'HTTP_USER_AGENT': 'silly-human'}
        )


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsLogLevelTestCase(BaseLogSettingsTestCase):
    def test_logging_default_debug_level(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request)
        self._assert_logged_with_level(mock_log, DEFAULT_LOG_LEVEL)

    @override_settings(REQUEST_LOGGING_DATA_LOG_LEVEL=logging.INFO)
    def test_logging_with_customized_log_level(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request)
        self._assert_logged_with_level(mock_log, logging.INFO)

    @override_settings(REQUEST_LOGGING_DATA_LOG_LEVEL=None)
    def test_invalid_log_level(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsColorizeTestCase(BaseLogSettingsTestCase):
    def test_default_colorize(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request)
        self.assertEquals(DEFAULT_COLORIZE, self._is_log_colorized(mock_log))

    @override_settings(REQUEST_LOGGING_DISABLE_COLORIZE=False)
    def test_disable_colorize(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request)
        self.assertFalse(self._is_log_colorized(mock_log))

    @override_settings(REQUEST_LOGGING_DISABLE_COLORIZE='Not a boolean')
    def test_invalid_colorize(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()

    @override_settings(REQUEST_LOGGING_DISABLE_COLORIZE=False)
    def test_disable_colorize(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request)
        self.assertFalse(self._is_log_colorized(mock_log))

    def _is_log_colorized(self, mock_log):
        reset_code = '\x1b[0m'
        calls = mock_log.log.call_args_list
        logs = " ".join(call[0][1] for call in calls)
        return reset_code in logs


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsMaxLengthTestCase(BaseLogTestCase):
    def test_default_max_body_length(self, mock_log):
        factory = RequestFactory()
        middleware = LoggingMiddleware()

        body = DEFAULT_MAX_BODY_LENGTH * "0" + "1"
        datafile = io.StringIO(body)
        request = factory.post("/somewhere", data={"file": datafile})
        middleware.process_request(request)
        self._assert_logged(mock_log, str(request.body[:DEFAULT_MAX_BODY_LENGTH]))
        self._assert_not_logged(mock_log, body)

    @override_settings(REQUEST_LOGGING_MAX_BODY_LENGTH=150)
    def test_customized_max_body_length(self, mock_log):
        factory = RequestFactory()
        middleware = LoggingMiddleware()

        body = 150 * "0" + "1"
        datafile = io.StringIO(body)
        request = factory.post("/somewhere", data={"file": datafile})
        middleware.process_request(request)
        self._assert_logged(mock_log, str(request.body[:150]))
        self._assert_not_logged(mock_log, body)

    @override_settings(REQUEST_LOGGING_MAX_BODY_LENGTH='Not an int')
    def test_invalid_max_body_length(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()
