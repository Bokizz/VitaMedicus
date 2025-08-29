from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from datetime import timedelta
from .serializers import PatientRegistrationSerializer, VerifyPhoneSerializer, ResendSMSSerializer, DoctorRegistrationSerializer, CustomTokenObtainPairSerializer
from .models import PhoneVerification,Doctor
from .permissions import NotBlacklisted
from rest_framework import generics, permissions
import smtplib # dodaj smtp za emajl da prakjash

class PatientRegistrationView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer
    permission_classes = [permissions.AllowAny]
class DoctorRegistrationView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Doctor.objects.all()
    serializer_class = DoctorRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        doctor = serializer.save()

        headers = self.get_success_headers(serializer.data)

        return Response({
            "message": "Успешно се регистриравте докторе. Останува на администраторот да ве автентицира.",
            "doctor_id": doctor.id,
            "authorized": doctor.authorized
        },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

class VerifyPhoneView(generics.GenericAPIView):
    permission_classes = [NotBlacklisted, permissions.AllowAny]
    serializer_class = VerifyPhoneSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        phone = serializer.validated_data['phone_number']

        try:
            verification_code = PhoneVerification.objects.get(
                user__phone_number=phone,
                code=code,
                is_used=False
            )
            if verification_code.expires_at < timezone.now():
                return Response(
                    {"error": "Временската валидност на кодот истече."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            verification_code.is_used = True
            verification_code.save()

            user = verification_code.user
            user.is_phone_verified = True
            user.save()

            return Response({"message": "Успешно се верифициравте!"})
        except PhoneVerification.DoesNotExist:
            return Response(
                {"error": "Невалиден код."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ResendSMSCodeView(generics.GenericAPIView):
    permission_classes = [NotBlacklisted, permissions.AllowAny]
    serializer_class = ResendSMSSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone_number']
        if not phone:
            return Response(
                {"error": "Телефонскиот број задолжително треба да се внесе!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        User = get_user_model()
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            return Response(
                {"error": "Корисникот не постои!"},
                status=status.HTTP_404_NOT_FOUND
            )

        if getattr(user, 'is_phone_verified', False):
            return Response(
                {"message": "Телефонскиот број веќе е верифициран"},
                status=status.HTTP_200_OK
            )

        existing = PhoneVerification.objects.filter(
            user=user, is_used=False
        ).order_by('-created_at').first()

        if existing and existing.expires_at > timezone.now():
            remaining_seconds = int(
                (existing.expires_at - timezone.now()).total_seconds()
            )
            return Response(
                {"error": f"Постоечкиот код е сѐ уште валиден, имате {remaining_seconds} секунди останато. Обидете се повторно!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        code = get_random_string(6, allowed_chars='0123456789')
        expires_at = timezone.now() + timedelta(minutes=15)
        PhoneVerification.objects.create(user=user, code=code, expires_at=expires_at)

        print(f"SMS CODE VERIFICATION: Верификациски код за корисникот со телефонски број {user.phone_number}:{code}")

        return Response(
            {"message": "Нов верификациски код е испратен!"},
            status=status.HTTP_200_OK
        )
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
