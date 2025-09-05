from django.urls import path
from .views import *

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name = 'registration'),
    path('register/doctor/', DoctorRegistrationView.as_view(), name = 'doctor-registration'),
    path('login/', LoginView.as_view(), name = 'login'),
    path('logout/', LogoutView.as_view(), name = 'logout'),

    path('verify-phone/', VerifyPhoneView.as_view(), name = 'verify-phone'),
    
    path('resend-sms/', ResendSMSCodeView.as_view(), name = 'resend-sms'),
    path('forgot-password/', ForgotPasswordView.as_view(),name = "forgot-password"),
    path('reset-password/', ResetPasswordView.as_view(), name = "reset-password"),
]