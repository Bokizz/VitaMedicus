from django.urls import path
from .views import *

urlpatterns = [
    path('<int:doctor_id>/subscribe/', subscribe_doctor, name = 'subscribe-doctor')
]