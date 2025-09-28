from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vitamedicus.settings")
app = Celery("vitamedicus")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

app.conf.beat_schedule = {
    "delete-expired-appointments": {
        "task": "appointments.tasks.delete_expired_appointments",
        "schedule": crontab(hour=0, minute=0),  
    },
    "generate_daily_slots" :{
        "task" : "appointments.tasks.generate_daily_slots",
        "schedule": crontab(hour=0, minute=0),
    },
    "auto_confirm_appointments": {
        "task" : "appointments.tasks.auto_confirm_appointments",
        "schedule" : 30.0,
    },
    "delete_unverified": {
        "task": "accounts.tasks.delete_unverified",
        "schedule" : 600.0,
    },
    "monitor_appointments_limits": {
        "task" : "appointments.tasks.monitor_appointment_limits",
        "schedule" : 60.0,
    },
}