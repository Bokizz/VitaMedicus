from celery import shared_task
from datetime import date
from .models import Appointment

@shared_task
def delete_expired_appointments():
    today = date.today()
    expired = Appointment.objects.filter(date__lt=today)
    count = expired.count()
    expired.delete()
    return f"{count} expired appointments deleted."
