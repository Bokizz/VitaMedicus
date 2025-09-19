from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.conf import settings
from .models import Appointment
from .serializers import *
from hospitals.models import *
from .utils.pdf_generator import generate_appointment_pdf
import os
import smtplib # dodaj smtp za emajl da prakjash
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from rest_framework.response import Response
from accounts.models import Doctor
from hospitals.models import Service
from accounts.models import User
from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone

def authentication_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/api/accounts/login/')  # Replace 'login' with your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper

@authentication_required    
def appointment_page(request):
    return render(request,"appointments/appointment.html")


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


class AvailableAppointmentsView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    # permission_classes = [IsAuthenticated] KOGA KJE DODADESH LOGIN SESSION

    def get_queryset(self):
        doctor_id = self.request.query_params.get("doctor")
        date = self.request.query_params.get("date")
        qs = Appointment.objects.filter(booked=False)

        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        if date:
            qs = qs.filter(date=date)

        return qs

class BookAppointmentView(generics.UpdateAPIView):
    serializer_class = AppointmentSerializer
    # permission_classes = [IsAuthenticated] KOGA KJE DODADESH LOGIN SESSION

    queryset = Appointment.objects.all()

    def update(self, request, *args, **kwargs):
        appointment = self.get_object()
        service_id = request.data.get("service")

        if appointment.booked:
            return Response({"error": "Веќе е букиран овој термин."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response({"error": "Invalid service ID."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check doctor actually offers this service
        if not appointment.doctor.doctor_services.filter(service=service, approved=True, available=True).exists():
            return Response({"error": "Докторот не го нуди овој сервис."},
                            status=status.HTTP_400_BAD_REQUEST)

        appointment.patient = request.user
        appointment.service = service
        appointment.booked = True
        appointment.status = "pending"
        appointment.save()

        return Response(AppointmentSerializer(appointment).data)