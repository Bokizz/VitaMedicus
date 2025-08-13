from django.urls import path
from .views import PatientRegistrationView, VerifyPhoneView, ResendSMSCodeView

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name = 'registration'),
    path('verify-phone/', VerifyPhoneView.as_view(), name = 'verify-phone'),
    path('resend-sms/', ResendSMSCodeView.as_view(), name = 'resend-sms'),
]