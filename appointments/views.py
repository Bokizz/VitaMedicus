from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.conf import settings
from .models import Appointment
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
from django.utils import timezone
from datetime import time, datetime, date, timedelta
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
def appointment_page(request):
    return render(request,"appointments/appointment.html")

@authentication_required    
def appointment_confirmation_page(request):
    return render(request, "appointments/appointment_confirmation.html")

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
        
        appointment.status = 'cancelled'
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