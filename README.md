django-request-logging
==========================

Plug django-request-logging into your Django project and you will have intuitive and color coded request/response payload logging, for both web requests and API requests

## Installing

```bash
$ pip install django-request-logging
```

Then add ```request_logging.middleware.LoggingMiddleware``` to your ```MIDDLEWARE_CLASSES```.

For example:

```
MIDDLEWARE_CLASSES = (
    ...,
    'django_cprofile_middleware.middleware.ProfilerMiddleware',
    ...,
)
```

## Details

Most of times you don't have to care about these details. But in case you need to dig deep:

* All logs are configured using logger name "django.request".
* If HTTP status code is between 400 - 599, URIs are logged at ERROR level, otherwise they are logged at INFO level.
* If HTTP status code is between 400 - 599, data are logged at ERROR level, otherwise they are logged at DEBUG level.

## Enjoy!

Email me with any questions: [kenneth.jiang@gmail.com](kenneth.jiang@gmail.com).
