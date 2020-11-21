import sys

from django.conf.urls import url
from django.http import HttpResponse
from django.views import View
from request_logging.decorators import no_logging
from rest_framework import viewsets, routers

# DRF 3.8.2 is used in python versions 3.4 and older, which needs special handling
IS_DRF_382 = sys.version_info <= (3, 4)


def general_resource(request):
    return HttpResponse(status=200, body="Generic repsonse entity")


class TestView(View):
    def get(self):
        return HttpResponse(status=200)

    @no_logging()
    def post(self, request):
        return HttpResponse(status=200)


@no_logging()
def view_func(request):
    return HttpResponse(status=200, body="view_func with no logging")


@no_logging("Custom message")
def view_msg(request):
    return HttpResponse(status=200, body="view_msg with no logging with a custom reason why")


@no_logging(silent=True)
def dont_log_silent(request):
    return HttpResponse(status=200, body="view_msg with silent flag set")


@no_logging("Empty response body")
def dont_log_empty_response_body(request):
    return HttpResponse(status=201)


class UnannotatedDRF(viewsets.ModelViewSet):
    @no_logging("DRF explicit annotation")
    def list(self, request):
        return HttpResponse(status=200, body="DRF Unannotated")

    @no_logging("Takes excessive amounts of time to log")
    def partial_update(self, request, *args, **kwargs):
        return HttpResponse(status=200, body="NO logging")


router = routers.SimpleRouter(trailing_slash=False)
if IS_DRF_382:
    last_arguments = {"base_name": "widgets"}
else:
    last_arguments = {"basename": "widgets"}

router.register(r"widgets", UnannotatedDRF, **last_arguments)

urlpatterns = [
    url(r"^somewhere$", general_resource),
    url(r"^test_class$", TestView.as_view()),
    url(r"^test_func$", view_func),
    url(r"^test_msg$", view_msg),
    url(r"^dont_log_empty_response_body$", dont_log_empty_response_body),
    url(r"^dont_log_silent$", dont_log_silent),
] + router.urls
