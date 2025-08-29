from django.urls import path
from . import views
urlpatterns = [
    path("<int:appointment_id>/download-pdf/", views.download_appointment_pdf, name = "download appointment pdf"),
]