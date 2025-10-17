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
    start_date = today + timedelta(days=1)
    end_date = today + timedelta(days=7)
    
    doctors = Doctor.objects.filter(authorized=True)
    
    total_generated = 0
    current_date = start_date
    
    print(f"=== Starting appointment generation for {start_date} to {end_date} ===")
    
    while current_date <= end_date:
        # Skip weekends (5 = Saturday, 6 = Sunday)
        if current_date.weekday() >= 5:
            print(f"\nSkipping {current_date} (weekend)")
            current_date += timedelta(days=1)
            continue
        
        daily_count = 0
        print(f"\nGenerating appointments for {current_date} ({current_date.strftime('%A')}):")
        
        for doctor in doctors:
            department_assignment = DoctorDepartmentAssignment.objects.filter(
                doctor=doctor, approved=True
            ).first()
            hospital = doctor.hospital if hasattr(doctor, "hospital") else None

            if not (department_assignment and hospital):
                continue
            
            department = department_assignment.department

            # Define working hours (8:00 AM to 4:00 PM)
            start = datetime.combine(current_date, time(8, 0))
            end = datetime.combine(current_date, time(16, 0))
            slot_length = timedelta(minutes=30)

            slots = []
            current = start
            
            while current < end:
                slot_start = current.time()
                slot_end = (current + slot_length).time()

                # Skip break time (10:00–10:30)
                if not (time(10, 0) <= slot_start < time(10, 30)):
                    slots.append(Appointment(
                        doctor=doctor,
                        service=None,
                        department=department,
                        hospital=hospital,
                        date=current_date,
                        start_time=slot_start,
                        end_time=slot_end,
                        booked=False,
                        status='available'
                    ))

                current += slot_length

            # Bulk create slots
            if slots:
                created_count = len(Appointment.objects.bulk_create(slots, ignore_conflicts=True))
                daily_count += created_count
                print(f"  - Dr. {doctor.user.get_full_name()}: {created_count} slots")
        
        total_generated += daily_count
        print(f"Total for {current_date}: {daily_count} appointments")
        
        # Move to next day
        current_date += timedelta(days=1)
    
    print(f"\n=== Generation completed ===")
    print(f"Total appointments generated: {total_generated}")
    print(f"Date range: {start_date} to {end_date}")
    
    return total_generated

@shared_task
def monitor_appointment_limits():
    """Monitor appointment limits and track violations"""
    today = timezone.now().date()
    
    patients = User.objects.filter(is_blacklisted=False)
    
    # You might want to create a UserProfile model to track violations
    # For now, we'll just log the violations
    
    for patient in patients:
        # Calculate current week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Count today's appointments
        today_count = Appointment.objects.filter(
            patient=patient,
            date=today,
            booked=True
        ).count()
        
        # Count this week's appointments
        week_count = Appointment.objects.filter(
            patient=patient,
            date__gte=week_start,
            date__lte=week_end,
            booked=True
        ).count()
        
        # Log violations
        if today_count > 3:
            patient.violation_count = patient.violation_count + 1
            logger.warning(
                f'Patient {patient.phone_number} exceeded daily limit: {today_count}/3 appointments on {today}'
            )
        
        if week_count > 10:
            patient.violation_count = patient.violation_count + 1
            logger.warning(
                f'Patient {patient.phone_number} exceeded weekly limit: {week_count}/10 appointments for week {week_start} to {week_end}'
            )
        if patient.violation_count > 6:
            patient.is_blacklisted = True

@shared_task
def auto_confirm_appointments():
    """Auto-confirm booked appointments"""
    appointments = Appointment.objects.filter(booked=True, status='pending')
    
    for appointment in appointments:
        appointment.status = 'confirmed'
        appointment.save()
        logger.info(f'Auto-confirmed appointment {appointment.id}')