from datetime import datetime, timedelta, time, date
from ..models import Appointment

def generate_daily_slots(app_date, doctor, service):
    today = date.today()
    if app_date < today or app_date > today + timedelta(days=90):
        return []  # outside of allowed booking range
    
    slots = []
    start = datetime.combine(app_date, time(8, 0))
    end = datetime.combine(app_date, time(16, 0))
    break_start = datetime.combine(app_date, time(10, 0))
    break_end = datetime.combine(app_date,time(10, 30))

    current = start
    while current < end:
        slot_end = current + timedelta(minutes = 30)

        if not(current >= break_start and slot_end <= break_end):
            slots.append((current, slot_end))

        current = slot_end
    
    booked = Appointment.objects.filter(
        doctor = doctor,
        service = service,
        date = app_date
    ).values_list("start_time",flat = True)

    booked_times = {
        datetime.combine(app_date, b).replace(second=0, microsecond=0) 
        for b in booked
        }

    available_slots = [
        slot for slot in slots if slot[0].replace(second=0, microsecond=0) not in booked_times
    ]
    return available_slots