from django.urls import path
from .views import *
urlpatterns = [
    path("<int:appointment_id>/download/", download_appointment_pdf, name = "download-appointment-pdf"),
    path("<int:appointment_id>/send-document/", send_document, name = "send-document"),

    # path("available-slots/", AvailableAppointmentsView.as_view(), name="available_appointments"),
    path("book-appointment/", book_appointment_page, name = "book-appointment"),
    path('available-time-slots/', AvailableTimeSlotsView.as_view(), name='available-time-slots'),
    path('find/', FindAppointmentView.as_view(), name='find-appointment'),
    path('cancel/<int:appointment_id>/', cancel_appointment, name='cancel-appointment'),
    path('complete/<int:appointment_id>/',complete_appointment, name = 'complete-appointment'),
    path('comment/', appointment_comment_page, name = 'comment-appointment'),

    path('appointments-history/', appointments_history_page, name= 'appointments-history'),
    path('patients-history/<int:patient_id>/', patients_history_page, name = 'patients-history'),

    path("book/<int:pk>/", BookAppointmentView.as_view(), name="book_appointment"),
    path('appointment-confirmation/', appointment_confirmation_page, name='appointment-confirmation'),

    path('my-appointments/', my_appointments_page, name='my-appointments'),
]