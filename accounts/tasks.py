from celery import shared_task
from datetime import date, datetime, timedelta, time
from django.utils import timezone
from .models import User

# Izbrishi korisnici koi ne se verificirale 1 chas od registracija
@shared_task
def delete_unverified():
    one_hour_ago = timezone.now() - timedelta(hours=1)
    unverified_users = User.objects.filter(
        is_phone_verified=False,
        date_joined__lt=one_hour_ago
    )
    for user in unverified_users:
            print(f"Deleting unverified user: {user.email} ({user.phone_number})")
    count = unverified_users.count()
    unverified_users.delete()
    
    return f"Deleted {count} unverified users older than 1 hour."