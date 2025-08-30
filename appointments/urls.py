from django.urls import path
from . import views
urlpatterns = [
    path("<int:appointment_id>/download-pdf/", views.download_appointment_pdf, name = "download appointment pdf"),
    path("<int:appointment_id>/send-document/", views.send_document, name = "send-document")
]