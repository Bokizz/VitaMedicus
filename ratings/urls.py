from django.urls import path
from .views import *

urlpatterns = [
    path('rate-doctor/', DoctorRatingCreateView.as_view(), name='rate-doctor'),
]