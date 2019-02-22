import os
from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings" if os.path.isfile('settings.py') else 'common.settings')

app = Celery()
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.task_routes = settings.TASK_ROUTES
app.conf.CELERY_TRACK_STARTED = True
