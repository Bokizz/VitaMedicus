from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vitamedicus.settings")
app = Celery("vitamedicus")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "delete-expired-appointments": {
        "task": "appointments.tasks.delete_expired_appointments",
        "schedule": crontab(hour=0, minute=0),  # runs daily at midnight
    },
    "generate_daily_slots" :{
        "task" : "appointments.tasks.generate_daily_slots",
        "schedule": crontab(hour=0, minute=0),
    },
    "delete_unverified": {
        "task": "accounts.tasks.delete_unverified",
        "schedule" : 600.0,
    },
}