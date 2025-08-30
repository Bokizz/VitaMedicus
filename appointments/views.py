from django.shortcuts import render
from django.http import FileResponse, Http404
from django.conf import settings
from .models import Appointment
from .utils.pdf_generator import generate_appointment_pdf
import os
import smtplib # dodaj smtp za emajl da prakjash
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from rest_framework.response import Response

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

    subject = "Вашиото термин - Упат"
    body = "Почитуван/а,\n\nВо прилог е вашиот термин.\n\nСо почит,\nВаш VitaMedicus"
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