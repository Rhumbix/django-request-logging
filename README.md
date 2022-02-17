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

Most of the times you don't have to care about these details. But in case you need to dig deep:

* All logs are configured using logger name "django.request".
* If HTTP status code is between 400 - 599, URIs are logged at ERROR level, otherwise they are logged at INFO level.
* If HTTP status code is between 400 - 599, data are logged at ERROR level, otherwise they are logged at DEBUG level.

See `REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL` setting to override this.


A `no_logging` decorator is included for views with sensitive data. This decorator allows control over logging behaviour of single views via the following parameters:
```
* value
    * False: the view does NOT log any activity at all (overrules settings of log_headers, log_body, log_response and automatically sets them to False).
    * True: the view logs incoming requests (potentially log headers, body and response, depending on their specific settings)
    * None: NO_LOGGING_DEFAULT_VALUE is used (can be defined in settings file as DJANGO_REQUEST_LOGGING_NO_LOGGING_DEFAULT_VALUE)
* msg
    * Reason for deactivation of logging gets logged instead of request itself (only if silent=True and value=False)
    * NO_LOGGING_MSG is used by default
* log_headers
    * False: request headers will not get logged
    * True: request headers will get logged (if value is True)
    * None: LOG_HEADERS_DEFAULT_VALUE is used (can be defined in settings file as DJANGO_REQUEST_LOGGING_LOG_HEADERS_DEFAULT_VALUE)
* no_header_logging_msg
    * Reason for deactivation of header logging gets logged instead of headers (only if silent=True and log_headers=False)
    * NO_HEADER_LOGGING_MSG is used by default
* log_body
    * False: request body will not get logged
    * True: request headers will get logged (if value is True)
    * None: LOG_BODY_DEFAULT_VALUE is used (can be defined in settings file as DJANGO_REQUEST_LOGGING_LOG_BODY_DEFAULT_VALUE)
* no_body_logging_msg
    * Reason for deactivation of body logging gets logged instead of body (only if silent=True and log_body=False)
    * NO_BODY_LOGGING_MSG is used by default
* log_response
    * False: response will not get logged
    * True: response will get logged (if value is True)
    * None: LOG_RESPONSE_DEFAULT_VALUE is used (can be defined in settings file as DJANGO_REQUEST_LOGGING_LOG_RESPONSE_DEFAULT_VALUE)
* no_response_logging_msg
    * Reason for deactivation of body logging gets logged instead of body (only if silent=True and log_body=False)
    * NO_RESPONSE_LOGGING_MSG is used by default
* silent
    * True: deactivate logging of alternative messages case parts of the logging are deactivated (request/header/body/response)
    * False: alternative messages for deactivated parts of logging (request/header/body/response) are logged instead
```

By default, value of Http headers `HTTP_AUTHORIZATION` and `HTTP_PROXY_AUTHORIZATION` are replaced wih `*****`. You can use `REQUEST_LOGGING_SENSITIVE_HEADERS` setting to override this default behaviour with your list of sensitive headers.

## Django settings
You can customized some behaves of django-request-logging by following settings in Django `settings.py`.
### REQUEST_LOGGING_DATA_LOG_LEVEL
By default, data will log in DEBUG level, you can change to other valid level (Ex. logging.INFO) if need.
### REQUEST_LOGGING_ENABLE_COLORIZE
It's enabled by default. If you want to log into log file instead of console, you may want to remove ANSI color. You can set `REQUEST_LOGGING_ENABLE_COLORIZE=False` to disable colorize.
### REQUEST_LOGGING_DISABLE_COLORIZE (Deprecated)
This legacy setting will still available, but you should't use this setting anymore. You should use `REQUEST_LOGGING_ENABLE_COLORIZE` instead.
We keep this settings for backward compatibility.
### REQUEST_LOGGING_MAX_BODY_LENGTH
By default, max length of a request body and a response content is cut to 50000 characters.
### REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL
By default, HTTP status codes between 400 - 499 are logged at ERROR level.  You can set `REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=logging.WARNING` (etc) to override this.
If you set `REQUEST_LOGGING_HTTP_4XX_LOG_LEVEL=logging.INFO` they will be logged the same as normal requests.
### REQUEST_LOGGING_SENSITIVE_HEADERS
The value of the headers defined in this settings will be replaced with `'*****'` to hide the sensitive information while logging. By default it is set as `REQUEST_LOGGING_SENSITIVE_HEADERS = ["HTTP_AUTHORIZATION", "HTTP_PROXY_AUTHORIZATION"]`
### DJANGO_REQUEST_LOGGING_LOGGER_NAME
Name of the logger that is used to log django.request occurrances with the new LoggingMiddleware. Defaults to "django.request".
### DJANGO_REQUEST_LOGGING_NO_LOGGING_DEFAULT_VALUE
Global default to activate/deactivate logging of all views. Can be overruled for each individual view by using the @no_logging decator's "value" parameter.
### DJANGO_REQUEST_LOGGING_LOG_HEADERS_DEFAULT_VALUE = True
Global default to activate/deactivate logging of request headers for all views. Can be overruled for each individual view by using the @no_logging decator's "log_headers" parameter.
### DJANGO_REQUEST_LOGGING_LOG_BODY_DEFAULT_VALUE = True
Global default to activate/deactivate logging of request bodys for all views. Can be overruled for each individual view by using the @no_logging decator's "log_body" parameter.
### DJANGO_REQUEST_LOGGING_LOG_RESPONSE_DEFAULT_VALUE = True
Global default to activate/deactivate logging of responses for all views. Can be overruled for each individual view by using the @no_logging decator's "log_response" parameter.


## Deploying, Etc.

### Maintenance

Use `pyenv` to maintain a set of virtualenvs for 2.7 and a couple versions of Python 3.
Make sure the `requirements-dev.txt` installs for all of them, at least until we give up on 2.7.
At that point, update this README to let users know the last version they can use with 2.7.

### Setup

- `pip install twine pypandoc pbr wheel`
- If `pypandoc` complains that `pandoc` isn't installed, you can add that via `brew` if you have Homebrew installed
- You will need a `.pypirc` file in your user root folder that looks like this:

```
    index-servers=
        testpypi
        pypi

    [testpypi]
    username = rhumbix
    password = password for dev@rhumbix.com at Pypi

    [pypi]
    username = rhumbix
    password = password for dev@rhumbix.com at Pypi
```

### Publishing

- Bump the version value in `request_logging/__init__.py`
- Run `python setup.py publish`
- Manually tag per the instructions in the output of that command
- TODO: add automagic `git tag` logic to the publish process
- TODO: setup 2FA at Pypi
