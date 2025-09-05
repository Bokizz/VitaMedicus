from django.urls import path
from .views import *
urlpatterns = [
    path("<int:appointment_id>/download/", download_appointment_pdf, name = "download appointment pdf"),
    path("<int:appointment_id>/send/", send_document, name = "send-document"),
     path("available/", AvailableAppointmentsView.as_view(), name="available_appointments"),
    path("book/<int:pk>/", BookAppointmentView.as_view(), name="book_appointment"),
]