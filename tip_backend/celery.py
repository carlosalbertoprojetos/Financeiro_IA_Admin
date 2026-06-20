import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tip_backend.settings.dev")

app = Celery("tip_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
