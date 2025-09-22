from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.conf import settings
from django.utils import timezone
from datetime import time, datetime, date, timedelta
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import *
from .serializers import *
from hospitals.models import *
from accounts.models import User, Doctor
from .utils.pdf_generator import generate_appointment_pdf

from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status

import logging
import os
import smtplib # dodaj smtp za emajl da prakjash


def authentication_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/api/accounts/login/')  # Replace 'login' with your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper

@authentication_required    
def book_appointment_page(request):
    return render(request,"appointments/appointment.html")

@authentication_required
def rate_appointment_page(request):
    return render(request,"")

@authentication_required
def doctor_schedule_page(request):
    if not hasattr(request.user, 'doctor'):
        return render(request, 'error.html', {'message': 'Само доктори може да го видат својот распоред.'})
    
    # Get selected week from request or default to current week
    selected_week = request.GET.get('week', None)
    if selected_week:
        try:
            selected_date = datetime.strptime(selected_week + '-1', '%Y-W%W-%w').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Calculate Monday of the selected week
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(5)]  # Monday to Friday
    
    # Generate week options for dropdown (current week and next 4 weeks)
    current_week = timezone.now().date().isocalendar()[1]
    current_year = timezone.now().year
    week_options = []
    
    for week_offset in range(0, 5):  # Current week + next 4 weeks
        week_num = current_week + week_offset
        year = current_year
        
        # Handle year transition
        if week_num > 52:
            week_num -= 52
            year += 1
        
        week_start = datetime.strptime(f'{year}-W{week_num}-1', '%G-W%V-%u').date()
        week_end = week_start + timedelta(days=4)  # Friday
        
        week_options.append({
            'value': f'{year}-W{week_num:02d}',
            'label': f'{week_start.strftime("%d.%m")} - {week_end.strftime("%d.%m.%Y")}',
            'selected': selected_date.isocalendar()[1] == week_num and selected_date.year == year
        })
    
    # Get all appointments for this doctor for the selected week
    appointments = Appointment.objects.filter(
        doctor=request.user.doctor,
        date__gte=start_of_week,
        date__lte=start_of_week + timedelta(days=4)
    ).select_related(
        'patient', 
        'service', 
        'hospital',
        'department'
    ).order_by('date', 'start_time')
    
    # Create time slots from 08:00 to 16:00 (30-minute intervals)
    time_slots = []
    for hour in range(8, 16):  # 8 AM to 4 PM
        for minute in [0, 30]:  # Every 30 minutes
            time_str = f"{hour:02d}:{minute:02d}"
            time_slots.append(time_str)
            
    # Organize appointments by date and time for easier template access
    schedule_dict = {}
    for date in week_dates:
        schedule_dict[str(date)] = {}
        for time_slot in time_slots:
            schedule_dict[str(date)][time_slot] = None
    
    for appointment in appointments:
        date_str = str(appointment.date)
        time_str = appointment.start_time.strftime('%H:%M')
        if date_str in schedule_dict and time_str in schedule_dict[date_str]:
            schedule_dict[date_str][time_str] = appointment
    
    # Convert to list of tuples for easier template iteration
    schedule_list = []
    for date in week_dates:
        date_str = str(date)
        day_appointments = []
        for time_slot in time_slots:
            appointment = schedule_dict[date_str].get(time_slot)
            day_appointments.append({
                'time_slot': time_slot,
                'appointment': appointment
            })
        schedule_list.append({
            'date': date,
            'date_str': date_str,
            'appointments': day_appointments,
            'display_date': date.strftime('%a, %b %d, %Y'),
            'tab_id': f'day{len(schedule_list) + 1}',
            'day_number': len(schedule_list) + 1,
            'is_today': date == timezone.now().date(),
            'day_name': ['Понеделник', 'Вторник', 'Среда', 'Четврток', 'Петок'][len(schedule_list)]
        })
    
    context = {
        'schedule_list': schedule_list,
        'time_slots': time_slots,
        'today': timezone.now().date(),
        'week_options': week_options,
        'selected_week': selected_date.strftime('%Y-W%W'),
        'week_range': f"{start_of_week.strftime('%d.%m.%Y')} - {(start_of_week + timedelta(days=4)).strftime('%d.%m.%Y')}"
    }
    
    return render(request, 'appointments/doctor_schedule.html', context)


@authentication_required
def my_appointments_page(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    
    appointments = Appointment.objects.filter(
        patient=request.user,
        booked=True
    )
    
    # Apply status filter
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    
    # Apply search filter
    if search_query:
        appointments = appointments.filter(
            Q(service__name__icontains=search_query) |
            Q(hospital__name__icontains=search_query) |
            Q(doctor__user__first_name__icontains=search_query) |
            Q(doctor__user__last_name__icontains=search_query)
        )
    
    # Order by date (most recent first)
    appointments = appointments.select_related(
        'service', 'hospital', 'doctor', 'doctor__user'
    ).order_by('-date', '-start_time')
    
    # Add pagination
    paginator = Paginator(appointments, 10)  # Show 10 appointments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Status options for filter dropdown
    status_choices = [
        ('', 'Филтер по статус'),
        ('pending', 'Чекање на потврда'),
        ('confirmed', 'Потврдено'),
        ('cancelled', 'Откажано'),
        ('finished', 'Завршено'),
    ]
    
    context = {
        'appointments': page_obj,
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': status_choices,
    }
    return render(request, "appointments/my_appointments.html", context)    

@authentication_required    
def appointment_confirmation_page(request):
    return render(request, "appointments/appointment_confirmation.html")

@authentication_required    
def cancel_appointment(request, appointment_id):
    try:
        appointment = Appointment.objects.get(
            id=appointment_id,
            patient=request.user,
            booked=True
        )
        
        # Check if appointment can be cancelled (at least 24h before)
        if not appointment.can_cancel():
            return JsonResponse({
                'success': False,
                'error': 'Терминот може да се откаже најмалку 24 часа пред почетокот.'
            })
        
        appointment.status = 'pending'
        appointment.patient = None
        appointment.booked = False
        appointment.save()
        
        return JsonResponse({'success': True})
        
    except Appointment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Терминот не е пронајден.'
        })

def download_appointment_pdf(request, appointment_id): # permissions.isAuthenticated dodaj posle test
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        raise Http404("Не постои тој термин.")

    file_path = generate_appointment_pdf(appointment)

    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))

def send_document(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id = appointment_id)
    except Appointment.DoesNotExist:
        raise Http404("Не постои тој термин.")
    pdf_path = generate_appointment_pdf(appointment)

    subject = "Вашиот термин - Упат"
    body = "Почитуван/а,\n\nВо прилог е вашиот упат.\n\nСо почит,\nВаш VitaMedicus"
    from_email = settings.EMAIL_HOST_USER
    # to_email = appointment.patient.email posle testing kje se stavi
    to_email = settings.EMAIL_HOST_USER

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))\
    
    #PDF dodavanje
    with open(pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

    #mejl prakjanjeto
    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(msg["From"], msg["To"], msg.as_string())
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    return Response({"message": "PDF е испратен на вашата е-пошта успешно!"})

class FindAppointmentView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    
    def get_queryset(self):
        doctor_id = self.request.query_params.get("doctor_id")
        date = self.request.query_params.get("date")
        time_range = self.request.query_params.get("time")
        
        if not all([doctor_id, date, time_range]):
            return Appointment.objects.none()
        
        try:
            # Parse time range (e.g., "08:00-08:30")
            start_time_str = time_range.split('-')[0]
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            
            # Parse date
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            
            return Appointment.objects.filter(
                doctor_id=doctor_id,
                date=date_obj,
                start_time=start_time,
                booked=False
            )
        except (ValueError, IndexError):
            return Appointment.objects.none()


class BookAppointmentView(generics.UpdateAPIView):
    serializer_class = AppointmentSerializer
    queryset = Appointment.objects.all()
    
    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        service_id = request.data.get("service_id")
        
        if appointment.booked:
            return Response({"error": "Веќе е букиран овој термин."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({"error": "Невалиден сервис ID."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        
        appointment.patient = request.user
        appointment.service = service
        appointment.booked = True
        appointment.status = "pending"
        appointment.save()
        
        return Response(AppointmentSerializer(appointment).data)


logger = logging.getLogger(__name__)

class AvailableTimeSlotsView(APIView):
    def get(self, request):
        try:
            doctor_id = request.GET.get('doctor_id')
            selected_date = request.GET.get('date')
            
            logger.info(f"Received request: doctor_id={doctor_id}, date={selected_date}")
            
            if not doctor_id or not selected_date:
                return Response({
                    "error": "Both doctor_id and date are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Parse the date
            appointment_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            
            logger.info(f"Looking for appointments for doctor {doctor_id} on {appointment_date}")
            
            # Get available appointments for this doctor on this date
            available_appointments = Appointment.objects.filter(
                doctor_id=doctor_id,
                date=appointment_date,
                booked=False
            ).order_by('start_time')
            
            logger.info(f"Found {available_appointments.count()} available appointments")
            
            # Format the response with time ranges
            time_slots = []
            for appointment in available_appointments:
                # Skip if it's during break time (10:00-10:30)
                if (appointment.start_time >= time(10, 0) and 
                    appointment.start_time < time(10, 30)):
                    logger.info(f"Skipping break time appointment: {appointment.start_time}")
                    continue
                
                # Format as "HH:MM-HH:MM"
                start_time_str = appointment.start_time.strftime('%H:%M')
                end_time_str = appointment.end_time.strftime('%H:%M')
                time_range = f"{start_time_str}-{end_time_str}"
                
                time_slots.append(time_range)
            
            logger.info(f"Returning {len(time_slots)} available time slots")
            
            return Response({
                'date': selected_date,
                'doctor_id': doctor_id,
                'available_slots': time_slots
            })
            
        except ValueError as e:
            logger.error(f"ValueError: {str(e)}")
            return Response({
                "error": "Invalid date format. Use YYYY-MM-DD"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({
                "error": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def complete_appointment(request, appointment_id):
    if not request.user.is_authenticated or not hasattr(request.user, 'doctor'):
        messages.error(request, "Немате дозвола да ја завршите оваа назнака.")
        return redirect('home')
    
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        doctor=request.user.doctor
    )
    
    # Mark appointment as finished
    appointment.status = 'finished'
    appointment.save()
    
    # Store appointment info in session for the comment page
    request.session['completed_appointment'] = {
        'id': appointment.id,
        'date': appointment.date.isoformat(),
        'time': appointment.start_time.isoformat(),
        'patient_id': appointment.patient.id,
        'patient_name': f"{appointment.patient.first_name} {appointment.patient.last_name}"
    }
    
    return redirect('comment-appointment')

def appointment_comment_page(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'doctor'):
        messages.error(request, "Немате дозвола да коментирате.")
        return redirect('home')
    
    # Get appointment info from session
    appointment_info = request.session.get('completed_appointment')
    if not appointment_info:
        messages.error(request, "Нема завршена назнака за коментирање.")
        return redirect('home')
    
    if request.method == 'POST':
        comment_text = request.POST.get('comment', '').strip()
        
        if comment_text:
            # Create the comment
            AppointmentComment.objects.create(
                appointment_date=appointment_info['date'],
                appointment_time=appointment_info['time'],
                doctor=request.user.doctor,
                patient_id=appointment_info['patient_id'],
                comment=comment_text
            )
            
            # Clear the session
            del request.session['completed_appointment']
            
            messages.success(request, "Коментарот е успешно зачуван.")
            return redirect('home')
        else:
            messages.error(request, "Ве молам внесете коментар.")
    
    context = {
        'patient_name': appointment_info.get('patient_name', ''),
        'appointment_date': appointment_info.get('date', ''),
        'appointment_time': appointment_info.get('time', ''),
    }
    
    return render(request, 'appointments/appointment_comment.html', context)

@authentication_required
def appointments_history_page(request):
    
    comments = AppointmentComment.objects.filter(
        patient=request.user
    ).select_related('doctor', 'doctor__user').order_by('-created_at')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        comments = comments.filter(
            Q(comment__icontains=search_query) |
            Q(doctor__user__first_name__icontains=search_query) |
            Q(doctor__user__last_name__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(comments, 10)  # Show 10 comments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'comments': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'appointments/appointments_history.html', context)

@authentication_required
def patients_history_page(request,patient_id):
    patient = get_object_or_404(User, id=patient_id)
    
    # Check if the current user is a doctor
    if not hasattr(request.user, 'doctor'):
        return redirect('home')
    
    if not patient.share_info:
        return redirect('home')

    # Filter comments for this specific patient
    comments = AppointmentComment.objects.filter(
        patient=patient  # Filter by the target patient, not the logged-in user
    ).select_related('doctor', 'doctor__user').order_by('-created_at')
    
    # Add search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        comments = comments.filter(
            Q(comment__icontains=search_query) |
            Q(doctor__user__first_name__icontains=search_query) |
            Q(doctor__user__last_name__icontains=search_query)
        )
    
    # Add pagination
    paginator = Paginator(comments, 10)  # Show 10 comments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'comments': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'patient': patient, 
    }
    
    return render(request, 'appointments/doctors_patient_history.html', context)
