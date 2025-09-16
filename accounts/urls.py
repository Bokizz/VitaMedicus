from django.urls import path
from .views import *

urlpatterns = [
    path('register/patient', PatientRegistrationView.as_view(), name = 'registration'),
    
    path('register/doctor/', DoctorRegistrationView.as_view(), name = 'doctor-registration'),

    path('register/', registration_page, name = 'register_page'),

    path('login/user', LoginView.as_view(), name = 'login'),
    path('login/', login_page, name= 'login_page'),
    path('logout/', LogoutView.as_view(), name = 'logout'),

    path('verify-phone/', VerifyPhoneView.as_view(), name = 'verify-phone'),
    path('verify/', verification_page, name = 'verify_page'),
    path('resend-sms/', ResendSMSCodeView.as_view(), name = 'resend-sms'),

    path('forgot-password/', ForgotPasswordView.as_view(),name = "forgot-password"),
    path('forgot-password-page/', forgot_password_page, name = "forgot-password_page"),

    path('reset-password/', ResetPasswordView.as_view(), name = "reset-password"),
    path('reset-password-page/', reset_password_page, name="reset-password_page"),

    path('departments/', departments_by_hospital, name="departments_by_hospital"),
    path('services/', services_by_department, name="services_by_department"),
]