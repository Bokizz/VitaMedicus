from django.urls import path
from .views import *

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name = 'registration'),
    path('verify-phone/', VerifyPhoneView.as_view(), name = 'verify-phone'),
    path('resend-sms/', ResendSMSCodeView.as_view(), name = 'resend-sms'),
    path('register/doctor/', DoctorRegistrationView.as_view(), name = 'doctor-registration'),
    path('login/', LoginView.as_view(), name = "login")
]