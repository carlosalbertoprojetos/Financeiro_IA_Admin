import os
from pathlib import Path

from dotenv import load_dotenv

from ai.openai_models import DEFAULT_OPENAI_MODEL

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-dev-secret-key")

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
    "integrations.trello",
    "analytics",
    "reports",
    "ai",
    "dashboard",
    "apps.integrations",
    "apps.data_sources",
    "apps.analytics",
    "apps.reports",
    "apps.dashboards",
    "apps.ai_insights",
    "apps.exports",
    "apps.users",
    "apps.settings",
    "apps.intelligence",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tip_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tip_backend.wsgi.application"
ASGI_APPLICATION = "tip_backend.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "tip_backend"),
        "USER": os.environ.get("POSTGRES_USER", "tip_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "tip_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

if os.environ.get("POCL_ENABLED", "false").lower() in ("true", "1", "yes"):
    from celery.schedules import crontab

    _pocl_board = os.environ.get("POCL_BOARD_ID", "")
    CELERY_BEAT_SCHEDULE = {
        "pocl-morning-cycle": {
            "task": "intelligence.pocl_daily_cycle",
            "schedule": crontab(hour=8, minute=0),
            "kwargs": {"board_id": _pocl_board, "phase": "morning"},
        },
        "pocl-intraday-cycle": {
            "task": "intelligence.pocl_daily_cycle",
            "schedule": crontab(hour="9-18", minute=0),
            "kwargs": {"board_id": _pocl_board, "phase": "intraday"},
        },
        "pocl-eod-cycle": {
            "task": "intelligence.pocl_daily_cycle",
            "schedule": crontab(hour=19, minute=0),
            "kwargs": {"board_id": _pocl_board, "phase": "eod"},
        },
        "pocl-measure-followups": {
            "task": "intelligence.pocl_measure_followups",
            "schedule": crontab(minute="*/30"),
            "kwargs": {"board_id": _pocl_board},
        },
    }

REDIS_CACHE_URL = os.environ.get("REDIS_CACHE_URL", "")

if REDIS_CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_CACHE_URL,
            "KEY_PREFIX": "eor",
            "TIMEOUT": 3600,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "eor-report-query",
        }
    }

TRELLO_API_KEY = os.environ.get("TRELLO_API_KEY", "")
TRELLO_API_TOKEN = os.environ.get("TRELLO_API_TOKEN", "")
INTEGRATION_CREDENTIALS_KEY = os.environ.get("INTEGRATION_CREDENTIALS_KEY", "")
INTEGRATION_QUEUE_BACKEND = os.environ.get("INTEGRATION_QUEUE_BACKEND", "local_db")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
