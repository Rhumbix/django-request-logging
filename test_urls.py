from django.conf.urls import url
from django.http import HttpResponse
from django.views import View
from request_logging.decorators import no_logging


class TestView(View):
    @no_logging()
    def post(self, request):
        return HttpResponse(status=200)


@no_logging()
def view_func(request):
    return HttpResponse(status=200, "view_func with no logging")


@no_logging('Custom message')
def view_msg(request):
    return HttpResponse(status=200, "view_msg with no logging with a custom reason why")


urlpatterns = [
    url(r'^test_class$', TestView.as_view()),
    url(r'^test_func$', view_func),
    url(r'^test_msg$', view_msg),
]
