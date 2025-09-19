from django.urls import path
from .views import *
urlpatterns = [
    path("<int:appointment_id>/download/", download_appointment_pdf, name = "download-appointment-pdf"),
    path("<int:appointment_id>/send-document/", send_document, name = "send-document"),

    # path("available-slots/", AvailableAppointmentsView.as_view(), name="available_appointments"),
    path("appointment/", appointment_page, name = "book-appointment"),
    path('available-time-slots/', AvailableTimeSlotsView.as_view(), name='available-time-slots'),
    path('find/', FindAppointmentView.as_view(), name='find-appointment'),
    path('cancel/<int:appointment_id>/', cancel_appointment, name='cancel-appointment'),

    path("book/<int:pk>/", BookAppointmentView.as_view(), name="book_appointment"),
    path('appointment-confirmation/', appointment_confirmation_page, name='appointment-confirmation'),
]