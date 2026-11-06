try:
    from django.urls import re_path as url  # Django >= 2.0
except ImportError:
    from django.conf.urls import url  # Django 1.11
from django.http import HttpResponse
from request_logging.decorators import no_logging


@no_logging()
def view_func(request):
    return HttpResponse(status=200, body="view_func with no logging")


urlpatterns = [
    url(r"^test_route$", view_func),
]
