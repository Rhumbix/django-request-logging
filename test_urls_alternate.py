from django.conf.urls import url
from django.http import HttpResponse
from request_logging.decorators import no_logging


@no_logging()
def view_func(request):
    return HttpResponse(status=200, body="view_func with no logging")


urlpatterns = [
    url(r"^test_route$", view_func),
]
