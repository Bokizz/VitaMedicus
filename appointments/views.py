from django.shortcuts import render
from django.http import FileResponse, Http404
from .models import Appointment
from .utils.pdf_generator import generate_appointment_pdf
import os
import smtplib # dodaj smtp za emajl da prakjash

def download_appointment_pdf(request, appointment_id): # permissions.isAuthenticated dodaj posle test
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        raise Http404("Не постои тој термин.")

    file_path = generate_appointment_pdf(appointment)

    return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
# Create your views here.
