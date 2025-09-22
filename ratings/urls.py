from django.urls import path
from .views import *

urlpatterns = [
    path('rate/<int:appointment_id>/', rate_doctor_hospital_page, name='rate'),
    path('doctor/ratings/', doctor_ratings, name='doctor-ratings'),
    path('hospital/ratings/', hospital_ratings, name='hospital-ratings'),
]