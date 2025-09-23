from django.shortcuts import render,redirect
from django.utils import timezone
from django.contrib.auth import get_user_model,login,logout,authenticate
from django.utils.crypto import get_random_string
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view

from email.mime.text import MIMEText
from datetime import timedelta

from .serializers import *
from .models import PhoneVerification,Doctor
from appointments.models import Appointment
from .permissions import NotBlacklisted
import smtplib

def authentication_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/api/accounts/login/')  # Replace 'login' with your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper

@authentication_required
def profile_page(request):
    return render(request,"accounts/profile.html")

@authentication_required
@csrf_exempt
def update_profile(request):
    try:
        user = request.user
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@authentication_required
@csrf_exempt
def update_security(request):
    try:
        user = request.user
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        share_info = request.POST.get('share_info') == 'on'
        
        requires_verification = False
        
        # Update phone number if changed
        if phone_number != user.phone_number:
            user.phone_number = phone_number
            user.is_verified = False  # Mark as unverified
            requires_verification = True
        
        # Update password if provided
        if password:
            user.set_password(password)
        
        # Update share information preference
        user.share_info = share_info
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'requires_verification': requires_verification,
            'message': 'Security settings updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
        
def verification_page(request):
    phone_number = request.GET.get('phone_number', '')
    context = {'phone_number': phone_number}
    return render(request, "accounts/verify.html",context)
def login_page(request):
    return render(request,"accounts/login.html")
def registration_page(request):
    return render(request,"accounts/register.html")
def forgot_password_page(request):
    return render(request, "accounts/forgot_password.html")
def reset_password_page(request):
    token = request.GET.get('token', '')
    
    if not token:
        return render(request, 'accounts/reset_password_error.html', {
            'error': 'Невалиден линк за ресетирање.'
        })
    context = {'token': token}
    return render(request, "accounts/reset_password.html",context)

@authentication_required
def home_page(request):
    from django.utils import timezone
    from datetime import date
    if hasattr(request.user, 'doctor'):
            # User is a doctor - show appointments where they are the doctor
            appointments = Appointment.objects.filter(
                doctor=request.user.doctor,
                booked=True,
                date__gte=timezone.now().date()
            ).select_related(
                'patient', 
                'service', 
                'hospital'
            ).order_by('date', 'start_time')
            
            context = {
                'appointments': appointments,
                'is_doctor': True
            }
    else:
        appointments = Appointment.objects.filter(
            patient=request.user,
            booked=True,
            date__gte=date.today()
        ).exclude(
            status='cancelled'
        ).select_related(
            'doctor', 
            'doctor__user', 
            'doctor__hospital', 
            'service'
        ).order_by('date', 'start_time')
        context = {
            'appointments': appointments,
            'today': timezone.now().date()
        }
    return render(request, "home.html",context)


class PatientRegistrationView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = PatientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Регистрацијата беше успешна! Проверете ја е-поштата за верификациски код."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
    
    
@api_view(['GET'])
def departments_by_hospital(request):
    hospital_id = request.query_params.get("hospital_id")
    if not hospital_id:
        return Response({"error": "hospital_id is required"}, status=400)

    departments = Department.objects.filter(hospital_id=hospital_id)
    serializer = DepartmentSerializer(departments, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def services_by_department(request):
    department_id = request.query_params.get("department_id")
    if not department_id:
        return Response({"error": "department_id is required"}, status=400)

    services = Service.objects.filter(department_id=department_id)
    serializer = ServiceSerializer(services, many=True)
    return Response(serializer.data)
    
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        phone_number = request.data.get("phone_number")
        password = request.data.get("password")

        user = authenticate(request, phone_number = phone_number, password = password)

        if user is None:
            return Response({
                "error" : "Невалидни податоци за најавување"},
            status=status.HTTP_401_UNAUTHORIZED
            )
        if user.is_blacklisted:
            return Response(
                {"error": "Блокирани сте и не можете да се најавите додека не ве одблокира администраторот!"},
                status=status.HTTP_403_FORBIDDEN
                )
        
        login(request, user)
        return Response({
            "message" : "Успешно се најавивте!",
            "redirect_url":"/api/accounts/home/",
            "user" : {
                "id" : user.id,
                "first_name" : user.first_name,
                "last_name" : user.last_name,
                "phone_number" : user.phone_number,
                "role" : user.role,
            }
        })
    
class LogoutView(APIView):
    def post(self,request):
        logout(request)

        return redirect('/api/accounts/login/')

class VerifyPhoneView(generics.GenericAPIView):
    permission_classes = [NotBlacklisted, permissions.AllowAny]# permissions.isAuthenticated dodaj posle test
    serializer_class = VerifyPhoneSerializer

    def post(self, request):
        print(f"Request data: {request.data}")  # Debugging
        print(f"Content type: {request.content_type}")  # Debugging
        
        # Handle both form data and JSON data
        if request.content_type == 'application/json':
            data = request.data
        else:
            data = request.data.dict()
        
        print(f"Processed data: {data}")  # Debugging
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
    permission_classes = [NotBlacklisted, permissions.AllowAny]# permissions.isAuthenticated dodaj posle test
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
        from_email = settings.EMAIL_HOST_USER
        # to_email = user.email  # za produkcija vaka

        to_email = settings.EMAIL_HOST_USER # za testiranje vaka 

            
        msg = MIMEText(f"Нов верификациски код за корисникот со телефонски број {user.phone_number}:{code}")
        msg["Subject"] = "VitaMedicus - нов верификациски код"
        msg["From"] = from_email
        msg["To"] = to_email

        try:
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print(f"SMS CODE VERIFICATION терминал: Верификациски код за корисникот со телефонски број {user.phone_number}:{code}")

        return Response(
            {"message": "Нов верификациски код е испратен!"},
            status=status.HTTP_200_OK
        )

class ForgotPasswordView(generics.GenericAPIView):
    permission_classes = [NotBlacklisted]# permissions.isAuthenticated dodaj posle test
    serializer_class = ForgotPasswordSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            token = serializer.save()

            reset_link = f"http://localhost:8000/api/accounts/reset-password-page/?token={token.token}/"
            serializer.validated_data["email"] = settings.EMAIL_HOST_USER # za testiranje

            from_email = settings.EMAIL_HOST_USER
            to_email = serializer.validated_data["email"]
            
            msg = MIMEText(f"""
            Почитувани,
            
            Поднесовте барање за промена на вашата лозинка.
            
            Ве молиме продолжете кон следниот линк за да ја промените вашата лозинка:
            {reset_link}
            
            Овој линк ќе биде валиден во наредните 24 часа.
            
            Доколку немате поднесено вакво барање, веднаш контактирајте поддршка за корисници.

            Со почит,
            Тимот на VitaMedicus
            """)
            
            msg['Subject'] = "VitaMedicus - Промена на лозинка"
            msg['From'] = from_email
            msg['To'] = to_email

            try:
                with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    server.starttls()
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    server.sendmail(msg["From"], [msg["To"]], msg.as_string())
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Password reset link sent to email."}, status=200)

        return Response(serializer.errors, status=400)
    
class ResetPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny] # authenticated posle testing da se dodade
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        # Debug: Print what data we're receiving
        
        token = request.POST.get("token", "").strip().rstrip("/")
        if not token:
            token = request.GET.get("token", "").strip().rstrip("/")
        
        # Debug: Print the token we received
        print(f"Token received: '{token}'")
        print(f"Request POST data: {request.POST}")
        
        if not token:
            return Response({"error": "Грешка. Обидете се повторно."}, status=400)

        try:
            reset_token = PasswordResetToken.objects.get(token=token)
        except PasswordResetToken.DoesNotExist:
            return Response({"error": "Невалиден обид, обидете се повторно."}, status=400)

        if reset_token.is_expired():
            return Response({"error": "Времето за промена на лозинка истече, обидете се повторно."}, status=400)

        serializer = self.get_serializer(data=request.POST, context={"reset_token": reset_token})
        if serializer.is_valid():
            serializer.save()
            reset_token.delete()  # remove token after successful use
            return Response({"message": "Успешно ја променивте вашата лозинка!"}, status=200)

        return Response(serializer.errors, status=400)



    