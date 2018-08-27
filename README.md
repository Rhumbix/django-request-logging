django-request-logging
==========================

Plug django-request-logging into your Django project and you will have intuitive and color coded request/response payload logging, for both web requests and API requests. Supports Django 1.8+.

## Installing

```bash
$ pip install django-request-logging
```

Then add ```request_logging.middleware.LoggingMiddleware``` to your ```MIDDLEWARE```.

For example:

```python
MIDDLEWARE = (
    ...,
    'request_logging.middleware.LoggingMiddleware',
    ...,
)
```

And configure logging in your app:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',  # change debug level as appropiate
            'propagate': False,
        },
    },
}
```

## Details

Most of times you don't have to care about these details. But in case you need to dig deep:

* All logs are configured using logger name "django.request".
* If HTTP status code is between 400 - 599, URIs are logged at ERROR level, otherwise they are logged at INFO level.
* If HTTP status code is between 400 - 599, data are logged at ERROR level, otherwise they are logged at DEBUG level.

See `REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL` setting to override this. 


A `no_logging` decorator is included for views with sensitive data.

## Django settings
You can customized some behaves of django-request-logging by following settings in Django `settings.py`.
### REQUEST_LOGGING_DATA_LOG_LEVEL
By default, data will log in DEBUG level, you can change to other valid level (Ex. logging.INFO) if need.
### REQUEST_LOGGING_ENABLE_COLORIZE
If you want to log into log file instead of console, you may want to remove ANSI color. You can set `REQUEST_LOGGING_ENABLE_COLORIZE=False` to disable colorize.
### REQUEST_LOGGING_DISABLE_COLORIZE (Deprecated)
This legacy setting will still available, but you should't use this setting anymore. You should use `REQUEST_LOGGING_ENABLE_COLORIZE` instead.
We keep this settings for backward compatibility. 
### REQUEST_LOGGING_MAX_BODY_LENGTH
By default, max length of a request body and a response content is cut to 50000 characters.
### REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL
By default, HTTP status codes between 400 - 499 are logged at ERROR level.  You can set `REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=logging.WARNING` (etc) to override this.
If you set `REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=logging.INFO` they will be logged the same as normal requests.
