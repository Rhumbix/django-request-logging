#! /usr/bin/env python
import io
import logging
import mock
import re
import unittest

from django.conf import settings
from django.test import RequestFactory, override_settings
from django.http import HttpResponse, StreamingHttpResponse

import request_logging
from request_logging.middleware import (
    LoggingMiddleware,
    DEFAULT_LOG_LEVEL,
    DEFAULT_COLORIZE,
    DEFAULT_MAX_BODY_LENGTH,
    NO_LOGGING_MSG,
    DEFAULT_HTTP_4XX_LOG_LEVEL,
    IS_DJANGO_VERSION_GTE_3_2_0,
)

settings.configure()


class BaseLogTestCase(unittest.TestCase):
    def _assert_logged(self, mock_log, expected_entry):
        calls = mock_log.log.call_args_list
        text = "".join([call[0][1] for call in calls])
        self.assertIn(expected_entry, text)

    def _assert_logged_with_key_value(self, mock_log, expected_key, expected_value):
        calls = mock_log.log.call_args_list
        text = "".join([call[0][1] for call in calls])
        self.assertIn(expected_key, text)
        self.assertEqual(expected_value, text.split(expected_key)[1][4 : len(expected_value) + 4])

    def _assert_logged_with_level(self, mock_log, level):
        calls = mock_log.log.call_args_list
        called_levels = set(call[0][0] for call in calls)
        self.assertIn(level, called_levels, "{} not in {}".format(level, called_levels))

    def _asset_logged_with_additional_args_and_kwargs(self, mock_log, additional_args, kwargs):
        calls = mock_log.log.call_args_list
        for call_args, call_kwargs in calls:
            additional_call_args = call_args[2:]
            self.assertTrue(
                additional_args == additional_call_args,
                "Expected {} to be {}".format(additional_call_args, additional_args),
            )
            self.assertTrue(kwargs == call_kwargs, "Expected {} to be {}".format(call_kwargs, kwargs))

    def _assert_not_logged(self, mock_log, unexpected_entry):
        calls = mock_log.log.call_args_list
        text = " ".join([call[0][1] for call in calls])
        self.assertNotIn(unexpected_entry, text)


@mock.patch.object(request_logging.middleware, "request_logger")
class MissingRoutes(BaseLogTestCase):
    def setUp(self):
        self.factory = RequestFactory()

        def get_response(request):
            response = mock.MagicMock()
            response.status_code = 200
            response.get.return_value = "application/json"
            headers = {"test_headers": "test_headers"}
            if IS_DJANGO_VERSION_GTE_3_2_0:
                response.headers = headers
            else:
                response._headers = headers
            return response

        self.middleware = LoggingMiddleware(get_response)

    def test_no_exception_risen(self, mock_log):
        body = u"some body"
        request = self.factory.post("/a-missing-route-somewhere", data={"file": body})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, body)


@mock.patch.object(request_logging.middleware, "request_logger")
class LogTestCase(BaseLogTestCase):
    def setUp(self):
        self.factory = RequestFactory()

        def get_response(request):
            response = mock.MagicMock()
            response.status_code = 200
            response.get.return_value = "application/json"
            headers = {"test_headers": "test_headers"}
            if IS_DJANGO_VERSION_GTE_3_2_0:
                response.headers = headers
            else:
                response._headers = headers
            return response

        self.middleware = LoggingMiddleware(get_response)

    def test_request_body_logged(self, mock_log):
        body = u"some body"
        request = self.factory.post("/somewhere", data={"file": body})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, body)

    def test_request_binary_logged(self, mock_log):
        body = u"some body"
        datafile = io.StringIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, "(binary data)")

    def test_request_jpeg_logged(self, mock_log):
        body = (
            b'--BoUnDaRyStRiNg\r\nContent-Disposition: form-data; name="file"; filename="campaign_carousel_img.jp'
            b'g"\r\nContent-Type: image/jpeg\r\n\r\n\xff\xd8\xff\xe1\x00\x18Exif\x00\x00II*\x00\x08\x00\x00\x00'
            b"\x00\x00\x00\x00\x00\x00\x00\x00\xff\xec\x00\x11Ducky\x00\x01\x00\x04\x00\x00\x00d\x00\x00\xff\xe1"
            b"\x03{http://ns.adobe.com/"
        )
        datafile = io.BytesIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, "(multipart/form)")

    def test_request_headers_logged(self, mock_log):
        request = self.factory.post("/somewhere", **{"HTTP_USER_AGENT": "silly-human"})
        self.middleware.process_request(request, None, request.body)
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "User-Agent")
        else:
            self._assert_logged(mock_log, "HTTP_USER_AGENT")

    def test_request_headers_sensitive_logged_default(self, mock_log):
        request = self.factory.post(
            "/somewhere", **{"HTTP_AUTHORIZATION": "sensitive-token", "HTTP_PROXY_AUTHORIZATION": "proxy-token"}
        )
        middleware = LoggingMiddleware()
        middleware.process_request(request, None, request.body)
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "Authorization")
            self._assert_logged_with_key_value(mock_log, "Authorization", "*****")
        else:
            self._assert_logged(mock_log, "HTTP_AUTHORIZATION")
            self._assert_logged_with_key_value(mock_log, "HTTP_AUTHORIZATION", "*****")
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "Proxy-Authorization")
            self._assert_logged_with_key_value(mock_log, "Proxy-Authorization", "*****")
        else:
            self._assert_logged(mock_log, "HTTP_PROXY_AUTHORIZATION")
            self._assert_logged_with_key_value(mock_log, "HTTP_PROXY_AUTHORIZATION", "*****")

    @override_settings(
        REQUEST_LOGGING_SENSITIVE_HEADERS=["Authorization"]
        if IS_DJANGO_VERSION_GTE_3_2_0
        else ["HTTP_AUTHORIZATION"]
    )
    def test_request_headers_sensitive_logged(self, mock_log):
        request = self.factory.post(
            "/somewhere",
            **{
                "HTTP_AUTHORIZATION": "sensitive-token",
                "HTTP_USER_AGENT": "silly-human",
                "HTTP_PROXY_AUTHORIZATION": "proxy-token",
            }
        )
        middleware = LoggingMiddleware()
        middleware.process_request(request, None, request.body)
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "Authorization")
            self._assert_logged_with_key_value(mock_log, "Authorization", "*****")
        else:
            self._assert_logged(mock_log, "HTTP_AUTHORIZATION")
            self._assert_logged_with_key_value(mock_log, "HTTP_AUTHORIZATION", "*****")
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "User-Agent")
            self._assert_logged_with_key_value(mock_log, "User-Agent", "silly-human")
        else:
            self._assert_logged(mock_log, "HTTP_USER_AGENT")
            self._assert_logged_with_key_value(mock_log, "HTTP_USER_AGENT", "silly-human")
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "Proxy-Authorization")
            self._assert_logged_with_key_value(mock_log, "Proxy-Authorization", "proxy-token")
        else:
            self._assert_logged(mock_log, "HTTP_PROXY_AUTHORIZATION")
            self._assert_logged_with_key_value(mock_log, "HTTP_PROXY_AUTHORIZATION", "proxy-token")

    def test_response_headers_logged(self, mock_log):
        request = self.factory.post("/somewhere")
        response = mock.MagicMock()
        response.get.return_value = "application/json"
        headers = {"test_headers": "test_headers"}
        if IS_DJANGO_VERSION_GTE_3_2_0:
            response.headers = headers
        else:
            response._headers = headers
        self.middleware.process_response(request, response)
        self._assert_logged(mock_log, "test_headers")

    def test_call_logged(self, mock_log):
        body = u"some body"
        request = self.factory.post("/somewhere", data={"file": body}, **{"HTTP_USER_AGENT": "silly-human"})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, body)
        self._assert_logged(mock_log, "test_headers")
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "User-Agent")
        else:
            self._assert_logged(mock_log, "HTTP_USER_AGENT")

    def test_call_binary_logged(self, mock_log):
        body = u"some body"
        datafile = io.StringIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile}, **{"HTTP_USER_AGENT": "silly-human"})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, "(binary data)")
        self._assert_logged(mock_log, "test_headers")
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "User-Agent")
        else:
            self._assert_logged(mock_log, "HTTP_USER_AGENT")

    def test_call_jpeg_logged(self, mock_log):
        body = (
            b'--BoUnDaRyStRiNg\r\nContent-Disposition: form-data; name="file"; filename="campaign_carousel_img.jp'
            b'g"\r\nContent-Type: image/jpeg\r\n\r\n\xff\xd8\xff\xe1\x00\x18Exif\x00\x00II*\x00\x08\x00\x00\x00'
            b"\x00\x00\x00\x00\x00\x00\x00\x00\xff\xec\x00\x11Ducky\x00\x01\x00\x04\x00\x00\x00d\x00\x00\xff\xe1"
            b"\x03{http://ns.adobe.com/"
        )
        datafile = io.BytesIO(body)
        request = self.factory.post("/somewhere", data={"file": datafile}, **{"HTTP_USER_AGENT": "silly-human"})
        self.middleware.__call__(request)
        self._assert_logged(mock_log, "(multipart/form)")
        self._assert_logged(mock_log, "test_headers")
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self._assert_logged(mock_log, "User-Agent")
        else:
            self._assert_logged(mock_log, "HTTP_USER_AGENT")

    def test_minimal_logging_when_streaming(self, mock_log):
        uri = "/somewhere"
        request = self.factory.get(uri)
        response = StreamingHttpResponse(status=200, streaming_content=b"OK", content_type="application/json")
        self.middleware.process_response(request, response=response)
        self._assert_logged(mock_log, "(data_stream)")


@mock.patch.object(request_logging.middleware, "request_logger")
class LoggingContextTestCase(BaseLogTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = LoggingMiddleware()

    def test_request_logging_context(self, mock_log):
        request = self.factory.post("/somewhere")
        self.middleware.process_request(request, None, request.body)
        self._asset_logged_with_additional_args_and_kwargs(
            mock_log, (), {"extra": {"request": request, "response": None}}
        )

    def test_response_logging_context(self, mock_log):
        request = self.factory.post("/somewhere")
        response = mock.MagicMock()
        response.get.return_value = "application/json"
        headers = {"test_headers": "test_headers"}
        if IS_DJANGO_VERSION_GTE_3_2_0:
            response.headers = headers
        else:
            response._headers = headers
        self.middleware.process_response(request, response)
        self._asset_logged_with_additional_args_and_kwargs(
            mock_log, (), {"extra": {"request": request, "response": response}}
        )

    def test_get_logging_context_extensibility(self, mock_log):
        request = self.factory.post("/somewhere")
        self.middleware._get_logging_context = lambda request, response: {
            "args": (1, True, "Test"),
            "kwargs": {"extra": {"REQUEST": request, "middleware": self.middleware}, "exc_info": True},
        }

        self.middleware.process_request(request, None, request.body)
        self._asset_logged_with_additional_args_and_kwargs(
            mock_log,
            (1, True, "Test"),
            {"extra": {"REQUEST": request, "middleware": self.middleware}, "exc_info": True},
        )


class BaseLogSettingsTestCase(BaseLogTestCase):
    def setUp(self):
        body = u"some body"
        datafile = io.StringIO(body)
        self.request = RequestFactory().post(
            "/somewhere", data={"file": datafile}, **{"HTTP_USER_AGENT": "silly-human"}
        )


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsLogLevelTestCase(BaseLogSettingsTestCase):
    def test_logging_default_debug_level(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request, None, self.request.body)
        self._assert_logged_with_level(mock_log, DEFAULT_LOG_LEVEL)

    @override_settings(REQUEST_LOGGING_DATA_LOG_LEVEL=logging.INFO)
    def test_logging_with_customized_log_level(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request, None, self.request.body)
        self._assert_logged_with_level(mock_log, logging.INFO)

    @override_settings(REQUEST_LOGGING_DATA_LOG_LEVEL=None)
    def test_invalid_log_level(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsHttp4xxAsErrorTestCase(BaseLogTestCase):
    def setUp(self):
        from django.urls import set_urlconf

        set_urlconf("test_urls")
        self.factory = RequestFactory()
        self.request = self.factory.get("/not-a-valid-url")

        response = mock.MagicMock()
        response.status_code = 404
        response.get.return_value = "application/json"
        headers = {"test_headers": "test_headers"}
        if IS_DJANGO_VERSION_GTE_3_2_0:
            response.headers = headers
        else:
            response._headers = headers

        self.response_404 = response

    def test_logging_default_http_4xx_error(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_response(self.request, self.response_404)
        self.assertEqual(DEFAULT_HTTP_4XX_LOG_LEVEL, logging.ERROR)
        self._assert_logged_with_level(mock_log, DEFAULT_HTTP_4XX_LOG_LEVEL)

    def test_logging_http_4xx_level(self, mock_log):
        for level in (logging.INFO, logging.WARNING, logging.ERROR):
            mock_log.reset_mock()
            with override_settings(REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=level):
                middleware = LoggingMiddleware()
                middleware.process_response(self.request, self.response_404)
                self._assert_logged_with_level(mock_log, level)

    @override_settings(REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=None)
    def test_invalid_log_level(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsColorizeTestCase(BaseLogSettingsTestCase):
    def test_default_colorize(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request, None, self.request.body)
        self.assertEqual(DEFAULT_COLORIZE, self._is_log_colorized(mock_log))

    @override_settings(REQUEST_LOGGING_ENABLE_COLORIZE=False)
    def test_disable_colorize(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request, None, self.request.body)
        self.assertFalse(self._is_log_colorized(mock_log))

    @override_settings(REQUEST_LOGGING_ENABLE_COLORIZE="Not a boolean")
    def test_invalid_colorize(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()

    @override_settings(REQUEST_LOGGING_DISABLE_COLORIZE=False)
    def test_legacy_settings(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request, None, self.request.body)
        self.assertFalse(self._is_log_colorized(mock_log))

    @override_settings(REQUEST_LOGGING_DISABLE_COLORIZE=False, REQUEST_LOGGING_ENABLE_COLORIZE=True)
    def test_legacy_settings_taking_precedence(self, mock_log):
        middleware = LoggingMiddleware()
        middleware.process_request(self.request, None, self.request.body)
        self.assertFalse(self._is_log_colorized(mock_log))

    def _is_log_colorized(self, mock_log):
        reset_code = "\x1b[0m"
        calls = mock_log.log.call_args_list
        logs = " ".join(call[0][1] for call in calls)
        return reset_code in logs


@mock.patch.object(request_logging.middleware, "request_logger")
class LogSettingsMaxLengthTestCase(BaseLogTestCase):
    def setUp(self):
        from django.urls import set_urlconf

        set_urlconf("test_urls")

        self.factory = RequestFactory()

        def get_response(request):
            response = mock.MagicMock()
            response.status_code = 200
            response.get.return_value = "application/json"
            headers = {"test_headers": "test_headers"}
            if IS_DJANGO_VERSION_GTE_3_2_0:
                response.headers = headers
            else:
                response._headers = headers
            return response

        self.get_response = get_response

    @override_settings(REQUEST_LOGGING_ENABLE_COLORIZE=False)
    def test_default_max_body_length(self, mock_log):
        body = DEFAULT_MAX_BODY_LENGTH * "0" + "1"
        request = self.factory.post("/somewhere", data={"file": body})
        middleware = LoggingMiddleware(self.get_response)
        middleware.__call__(request)

        request_body_str = request.body if isinstance(request.body, str) else request.body.decode()
        self._assert_logged(mock_log, re.sub(r"\r?\n", "", request_body_str[:DEFAULT_MAX_BODY_LENGTH]))
        self._assert_not_logged(mock_log, body)

    @override_settings(REQUEST_LOGGING_MAX_BODY_LENGTH=150, REQUEST_LOGGING_ENABLE_COLORIZE=False)
    def test_customized_max_body_length(self, mock_log):
        body = 150 * "0" + "1"
        request = self.factory.post("/somewhere", data={"file": body})
        middleware = LoggingMiddleware(self.get_response)
        middleware.__call__(request)

        request_body_str = request.body if isinstance(request.body, str) else request.body.decode()
        self._assert_logged(mock_log, re.sub(r"\r?\n", "", request_body_str[:150]))
        self._assert_not_logged(mock_log, body)

    @override_settings(REQUEST_LOGGING_MAX_BODY_LENGTH="Not an int")
    def test_invalid_max_body_length(self, mock_log):
        with self.assertRaises(ValueError):
            LoggingMiddleware()


@mock.patch.object(request_logging.middleware, "request_logger")
class DecoratorTestCase(BaseLogTestCase):
    def setUp(self):
        from django.urls import set_urlconf

        set_urlconf("test_urls")
        self.factory = RequestFactory()
        self.middleware = LoggingMiddleware()

    def test_no_logging_decorator_class_view(self, mock_log):
        body = u"some super secret body"
        request = self.factory.post("/test_class", data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, body)
        self._assert_logged(mock_log, NO_LOGGING_MSG)

    def test_no_logging_decorator_func_view(self, mock_log):
        body = u"some super secret body"
        request = self.factory.post("/test_func", data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, body)
        self._assert_logged(mock_log, NO_LOGGING_MSG)

    def test_no_logging_decorator_custom_msg(self, mock_log):
        body = u"some super secret body"
        request = self.factory.post("/test_msg", data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, body)
        self._assert_not_logged(mock_log, NO_LOGGING_MSG)
        self._assert_logged(mock_log, "Custom message")

    def test_no_logging_decorator_silent(self, mock_log):
        body = u"some super secret body"
        request = self.factory.post("/dont_log_silent", data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, body)
        self._assert_not_logged(mock_log, NO_LOGGING_MSG)
        self._assert_not_logged(mock_log, "not logged because")

    def test_no_logging_empty_response_body(self, mock_log):
        body = u"our work of art"
        request = self.factory.post("/dont_log_empty_response_body", data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, body)
        self._assert_not_logged(mock_log, NO_LOGGING_MSG)
        self._assert_logged(mock_log, "Empty response body")

    def test_no_logging_alternate_urlconf(self, mock_log):
        body = u"some super secret body"
        request = self.factory.post("/test_route", data={"file": body})
        request.urlconf = "test_urls_alternate"
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, body)
        self._assert_logged(mock_log, NO_LOGGING_MSG)

    def test_still_logs_verb(self, mock_log):
        body = u"our work of art"
        request = self.factory.post("/dont_log_empty_response_body", data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_logged(mock_log, "POST")

    def test_still_logs_path(self, mock_log):
        body = u"our work of art"
        uri = "/dont_log_empty_response_body"
        request = self.factory.post(uri, data={"file": body})
        self.middleware.process_request(request, None, request.body)
        self._assert_logged(mock_log, uri)


@mock.patch.object(request_logging.middleware, "request_logger")
class DRFTestCase(BaseLogTestCase):
    def setUp(self):
        from django.urls import set_urlconf

        set_urlconf("test_urls")
        self.factory = RequestFactory()
        self.middleware = LoggingMiddleware()

    def test_no_request_logging_is_honored(self, mock_log):
        uri = "/widgets"
        request = self.factory.get(uri)
        self.middleware.process_request(request, None, request.body)
        self._assert_logged(mock_log, "DRF explicit annotation")

    def test_no_response_logging_is_honored(self, mock_log):
        uri = "/widgets"
        request = self.factory.get(uri)
        mock_response = HttpResponse('{"example":"response"}', content_type="application/json", status=422)
        self.middleware.process_response(request, response=mock_response)
        self._assert_not_logged(mock_log, '"example":"response"')
        self._assert_logged(mock_log, "/widgets")

    def test_non_existent_drf_route_logs(self, mock_log):
        uri = "/widgets/1234"
        request = self.factory.patch(uri, data={"almost": "had you"})
        self.middleware.process_request(request, None, request.body)
        self._assert_not_logged(mock_log, "almost")
        self._assert_not_logged(mock_log, "had you")


@mock.patch.object(request_logging.middleware, "request_logger")
class LogRequestAtDifferentLevelsTestCase(BaseLogTestCase):
    def setUp(self):
        from django.urls import set_urlconf

        set_urlconf("test_urls")
        self.factory = RequestFactory()

        self.request_200 = self.factory.get("/fine-thank-you")
        self.response_200 = mock.MagicMock()
        self.response_200.status_code = 200
        self.response_200.get.return_value = "application/json"
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self.response_200.headers = {"test_headers": "test_headers"}
        else:
            self.response_200._headers = {"test_headers": "test_headers"}

        self.request_404 = self.factory.get("/not-a-valid-url")
        self.response_404 = mock.MagicMock()
        self.response_404.status_code = 404
        self.response_404.get.return_value = "application/json"
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self.response_404.headers = {"test_headers": "test_headers"}
        else:
            self.response_404._headers = {"test_headers": "test_headers"}

        self.request_500 = self.factory.get("/bug")
        self.response_500 = mock.MagicMock()
        self.response_500.status_code = 500
        self.response_500.get.return_value = "application/json"
        if IS_DJANGO_VERSION_GTE_3_2_0:
            self.response_500.headers = {"test_headers": "test_headers"}
        else:
            self.response_500._headers = {"test_headers": "test_headers"}

    def test_log_request_200(self, mock_log):
        mock_log.reset_mock()
        middleware = LoggingMiddleware()
        middleware.process_request(self.request_200, self.response_200, self.request_200.body)
        self._assert_logged_with_level(mock_log, DEFAULT_LOG_LEVEL)

    def test_log_request_404_as_4xx(self, mock_log):
        for level in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR):
            mock_log.reset_mock()
            with override_settings(REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=level):
                middleware = LoggingMiddleware()
                middleware.process_request(self.request_404, self.response_404, self.request_404.body)
                self._assert_logged_with_level(mock_log, level)

    def test_log_request_500_as_error(self, mock_log):
        mock_log.reset_mock()
        middleware = LoggingMiddleware()
        middleware.process_request(self.request_500, self.response_500, self.request_500.body)
        self._assert_logged_with_level(mock_log, logging.ERROR)


if __name__ == "__main__":
    unittest.main()
