from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework import status

from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from django.conf import settings

from datetime import timedelta
from .models import PhoneVerification, User, Doctor, PasswordResetToken
from hospitals.models import *
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class PatientRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(
        write_only=True,
        label="Потврди лозинка",
        style={'input_type': 'password'}
    )
    class Meta:
        model = User
        fields = ['first_name', 
                  'last_name',
                  'email', 
                  'phone_number', 
                  'serial_number', 
                  'password',
                  'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True, 'label': 'Лозинка', 'style' : {'input_type': 'password'}},
            'first_name': {'label': 'Име'},
            'last_name': {'label': 'Презиме'},
            'email' : {'label' : 'Електронска пошта'},
            'phone_number': {'label': 'Телефонски број'},
            'serial_number': {'label': 'Матичен број'},
        }
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Не соодветствуваат лозинките! Обидете се повторно."})
        return attrs        

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            phone_number = validated_data['phone_number'],
            email = validated_data['email'],
            serial_number = validated_data['serial_number'],
            password = validated_data['password'],
            role = 'patient',
            is_active = True
        )
        user.set_password(validated_data['password'])
        user.save()

        code = get_random_string(6,allowed_chars = '0123456789')
        PhoneVerification.objects.create(
            user = user,
            code = code,
            created_at = timezone.now(),
            expires_at = timezone.now() + timedelta(minutes=15)
        )
        # SMS Ne raboti vo MK :(
        # from_email = settings.EMAIL_HOST_USER 
        # to_phone = '+38978339020@tmomail.net' 
        # msg = MIMEMultipart() 
        # msg["Subject"] = "Верификациски код \n" 
        # body = f"SMS CODE VERIFICATION: Верификациски код за корисникот со телефонски број {user.phone_number}:{code} \n" 
        # msg["From"] = from_email 
        # msg["To"] = to_phone 
        # msg.attach(MIMEText(body, 'plain')) 
        # sms = msg.as_string() 
        # try: 
        #     with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server: 
        #         server.starttls() 
        #         server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD) 
        #         server.sendmail(msg["From"], [msg["To"]], sms) 
        # except Exception as e: 
        #     return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print(f"SMS CODE VERIFICATION: Верификациски код за корисникот со телефонски број {user.phone_number}:{code}")
        

        return user

class VerifyPhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=12,
        help_text="Внесете го телефонскиот број во формат +3897XXXXXXX",
        label="Телефонски број"
    )
    code = serializers.CharField(
        max_length=6,
        help_text="Внесете го 6-цифрениот код што ви беше пратен по SMS",
        label = "Верификациски код"
    )
    
    def validate_phone_number(self, value):
        pattern = r"^\+3897\d{7}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Невалиден телефонски број!")
        return value
    
    def validate_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Кодот мора да е 6 цифри долг")
        return value


class ResendSMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField(
        max_length=12,
        help_text="Внесете го телефонскиот број во формат +3897XXXXXXX",
        label="Телефонски број"
    )

    def validate_phone_number(self, value):
        pattern = r"^\+3897\d{7}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Невалиден телефонски број!")
        return value
    
class DoctorRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source = "user.first_name", label = "Име")
    last_name = serializers.CharField(source = "user.last_name", label = "Презиме")
    phone_number = serializers.CharField(source = "user.phone_number",max_length = 12, label="Телефонски број")
    email = serializers.CharField(source = "user.email", max_length = 50, label = "Електронска пошта")
    serial_number = serializers.CharField(source = "user.serial_number",max_length = 13, label = "Матичен број")
    password = serializers.CharField(source = "user.password",write_only = True, label = "Лозинка",style = {'input_type': 'password'})
    confirm_password = serializers.CharField(
        write_only=True,
        label="Потврди лозинка",
        style={'input_type': 'password'}
    )
    specialization = serializers.ChoiceField(
        choices = Doctor._meta.get_field('specialization').choices,
        label = "Специјализација"
    )
    hospital = serializers.PrimaryKeyRelatedField(
        queryset = Hospital.objects.all(),
        label = "Назначена клиника"
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset = Department.objects.all(),
        write_only = True,
        label = "Назначено одделение"
    )
    service = serializers.PrimaryKeyRelatedField(
        queryset = Service.objects.all(),
        write_only = True,
        label = "Назначена услуга"
    )

    class Meta:
        model = Doctor
        fields = ['first_name', 
                  'last_name', 
                  'email',
                  'phone_number',
                  'serial_number',
                  'password',
                  'confirm_password',
                  'specialization',
                  'hospital',
                  'department',
                  'service']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Не соодветствуваат лозинките! Обидете се повторно."})
        return attrs
      
    def create(self, validated_data):
        user_data = validated_data.pop("user")
        first_name = user_data.pop("first_name")
        last_name = user_data.pop("last_name")
        email = user_data.pop("email")
        phone_number = user_data.pop("phone_number")
        serial_number = user_data.pop("serial_number")
        password = user_data.pop("password")
    
        hospital = validated_data.pop("hospital")
        department = validated_data.pop("department")
        specialization = validated_data.pop("specialization")
        service = validated_data.pop("service")

        user = User.objects.create_user(
            first_name = first_name,
            last_name = last_name,
            email = email,
            phone_number = phone_number,
            serial_number =  serial_number,
            password = password,
            role = 'doctor',
            is_active = True,
            is_staff = True
        )
        user.set_password(password)
        user.save()
        doctor = Doctor.objects.create(
            user = user,
            specialization = specialization,
            hospital = hospital,
            authorized = False
        )
        doctor.save()

        DoctorDepartmentAssignment.objects.create(
            doctor = doctor,
            department = department,
            approved = False
        )

        DoctorServiceAssignment.objects.create(
            doctor = doctor,
            service = service,
            approved = False
        )
            
        print(f"Pending admin approval...")
        return doctor 
    
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     username_field = "phone_number"
    
#     def validate(self, attrs):
#         data = super().validate(attrs)

#         if self.user.is_blacklisted:
#             raise AuthenticationFailed("Блокирани сте и не можете да се најавите додека не ве одблокира админ.")
    
#         data.update({
#             "user":{
#                 "id": self.user.id,
#                 "first_name": self.user.first_name,
#                 "last_name": self.user.last_name,
#                 "phone_number": self.user.phone_number,
#                 "role": self.user.role,
#             }
#         })
#         return data
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email = value).exists():
            raise serializers.ValidationError("Корисник со оваја електронска пошта не постои! Обидете се повторно.")
        return value
    
    def save(self):
        user = User.objects.get(email = self.validated_data["email"])
        token = PasswordResetToken.objects.create(user = user)

        return token
    
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only = True, style = {'input_type': 'password'})
    confirm_password = serializers.CharField(write_only = True, style = {'input_type': 'password'})

    def validate(self, attrs):
        reset_token = self.context.get("reset_token")
        if not reset_token:
            raise serializers.ValidationError("Токенот не е валиден. Обидете се повторно.")

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Не соодветствуваат лозинките! Обидете се повторно."})        
        
        user = reset_token.user

        if user.check_password(attrs["new_password"]):
            raise serializers.ValidationError(
                {"new_password": "Новата лозинка не смее да биде иста како старата."}
            )
        
        attrs["user"] = user
        return attrs
    
    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save()