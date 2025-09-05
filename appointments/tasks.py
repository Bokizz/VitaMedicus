from celery import shared_task
from datetime import date, datetime, timedelta, time
from django.utils import timezone
from .models import Appointment
from accounts.models import Doctor
from hospitals.models import Service, Department, Hospital, DoctorDepartmentAssignment


@shared_task
def delete_expired_appointments():
    today = date.today()
    expired = Appointment.objects.filter(date__lt=today)
    count = expired.count()
    expired.delete()
    return f"{count} expired appointments deleted."
@shared_task
def generate_daily_slots():
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)  # generiraj za naredniot den

    doctors = Doctor.objects.all()
    for doctor in doctors:
        
        department_assignment = DoctorDepartmentAssignment.objects.filter(
            doctor=doctor, approved=True
        ).first()
        hospital = doctor.hospital if hasattr(doctor, "hospital") else None

        if not (department_assignment and hospital):
            continue  # nema termini za doktori so potvrdeno oddelenie ili servis
        
        department = department_assignment.department

        start = datetime.combine(tomorrow, time(8, 0))
        end = datetime.combine(tomorrow, time(16, 0))
        slot_length = timedelta(minutes=30)

        slots = []
        current = start
        while current < end:
            slot_start = current.time()
            slot_end = (current + slot_length).time()

            # Pauza 10:00–10:30 , skipni
            if not (time(10, 0) <= slot_start < time(10, 30)):
                slots.append(Appointment(
                    doctor=doctor,
                    service=None, # Koga kje se bookira togash kje odbere pacientot koj servis go posakuva
                    department=department,
                    hospital=hospital,
                    date=tomorrow,
                    start_time=slot_start,
                    end_time=slot_end,
                    booked=False
                ))

            current += slot_length

        # Bulk create slots (skip existing duplicates)
        Appointment.objects.bulk_create(slots, ignore_conflicts=True)