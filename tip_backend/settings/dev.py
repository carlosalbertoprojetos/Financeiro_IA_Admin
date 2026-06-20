from .base import *  # noqa: F403

DEBUG = True

REST_FRAMEWORK = {  # noqa: F405
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        *REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"],  # noqa: F405
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
