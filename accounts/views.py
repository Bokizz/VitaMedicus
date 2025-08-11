from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone
from .serializers import PatientRegistrationSerializer
from .models import PhoneVerification

class PatientRegistrationView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer

class VerifyPhoneView(generics.GenericAPIView):
    def post(self, request):
        code = request.data.get('code')
        phone = request.data.get('phone_number')

        try:
            verification_code = PhoneVerification.objects.get(
                user__phone_number = phone, code = code , is_used = False# so __ se zemaa atributi ili metodi od klasa koi ne se nameneti da se overridenati ili direktno pristapeni
            )
            if verification_code.expires_at < timezone.now():
                return Response({"error":"Временската валидност на кодот истече."}, status = status.HTTP_400_BAD_REQUEST)
            
            verification_code.is_used = True
            verification_code.save()

            user = verification_code.user
            user.is_phone_verified = True
            user.save()

            return Response({"message":"Успешно се верифициравте!"})
        except PhoneVerification.DoesNotExist:
            return Response({"error":"Невалиден код."},status = status.HTTP_400_BAD_REQUEST)
# Create your views here.
