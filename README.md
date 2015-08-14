django-request-logging
==========================

## Installing

```bash
$ pip install django-request-logging
```

Then add ```request_logging.middleware.LoggingMiddleware``` to your ```MIDDLEWARE_CLASSES```. 

For example:

```
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'startup.do.work.FindProductMarketFitMiddleware',
    ...
    'django_cprofile_middleware.middleware.ProfilerMiddleware'
)
```

## Enjoy!

Email me with any questions: [kenneth.jiang@gmail.com](kenneth.jiang@gmail.com).
