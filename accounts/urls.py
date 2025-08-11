from django.urls import path
from .views import PatientRegistrationView, VerifyPhoneView

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name = 'registration'),
    path('verify-phone/', VerifyPhoneView.as_view(), name = 'verify-phone'),
]