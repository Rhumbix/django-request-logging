import sys

from django.conf.urls import url
from django.http import HttpResponse
from django.views import View
from request_logging.decorators import no_logging
from rest_framework import viewsets, routers

IS_PYTHON_27 = sys.version_info[0] < 3


def general_resource(request):
    return HttpResponse(status=200, body='Generic repsonse entity')


class TestView(View):
    def get(self):
        return HttpResponse(status=200)

    @no_logging()
    def post(self, request):
        return HttpResponse(status=200)


@no_logging()
def view_func(request):
    return HttpResponse(status=200, body="view_func with no logging")


@no_logging('Custom message')
def view_msg(request):
    return HttpResponse(status=200, body="view_msg with no logging with a custom reason why")


@no_logging('Empty response body')
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
if IS_PYTHON_27:
    last_arguments = {
        "base_name": "widgets"
    }
else:
    last_arguments = {
        "basename": "widgets"
    }

router.register(r"widgets", UnannotatedDRF, **last_arguments)

urlpatterns = [
    url(r'^somewhere$', general_resource),
    url(r'^test_class$', TestView.as_view()),
    url(r'^test_func$', view_func),
    url(r'^test_msg$', view_msg),
    url(r'^dont_log_empty_response_body$', dont_log_empty_response_body),
] + router.urls
