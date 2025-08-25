from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model, authenticate
from django.utils import timezone
from datetime import timedelta
from .models import PhoneVerification, User, Doctor
from hospitals.models import Hospital, Department, DoctorDepartmentAssignment
import re


class PatientRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'serial_number', 'password']
        extra_kwargs = {
            'password':{'write_only':True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name = validated_data['first_name'],
            last_name = validated_data['last_name'],
            phone_number = validated_data['phone_number'],
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
        print(f"SMS CODE VERIFICATION: Верификациски код за корисникот со телефонски број {user.phone_number}:{code}")
        return user

class VerifyPhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length = 12)
    code = serializers.CharField(max_length = 6)
    
    def validate_phone_number(self, value):
        pattern = r"^\+3897\d{7}$"
        if not re.match(pattern,value):
            raise serializers.ValidationError("Невалиден телефонски број!")
        return value
    
    def validate_code(self, value):
        if not value.isdigit() or len(value) != 6:
            raise serializers.ValidationError("Кодот мора да е 6 цифри долг")
        return value
    
class ResendSMSSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length = 12)

    def validate_phone_number(self, value):
        pattern = r"^\+3897\d{7}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError("Невалиден телефонски број!")
        return value

class DoctorRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source = "user.first_name")
    last_name = serializers.CharField(source = "user.last_name")
    phone_number = serializers.CharField(source = "user.phone_number",max_length = 12)
    serial_number = serializers.CharField(source = "user.serial_number",max_length = 13)
    password = serializers.CharField(source = "user.password",write_only = True)

    specialization = serializers.ChoiceField(
        choices = Doctor._meta.get_field('specialization').choices
    )
    hospital = serializers.PrimaryKeyRelatedField(
        queryset = Hospital.objects.all()
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset = Department.objects.all(),
        write_only = True
    )

    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'phone_number','serial_number',
                  'password','specialization','hospital','department']

    def create(self, validated_data):
        user_data = validated_data.pop("user")
        first_name = user_data.pop("first_name")
        last_name = user_data.pop("last_name")
        phone_number = user_data.pop("phone_number")
        serial_number = user_data.pop("serial_number")
        password = user_data.pop("password")
    
        hospital = validated_data.pop("hospital")
        department = validated_data.pop("department")
        specialization = validated_data.pop("specialization")


        user = User.objects.create_user(
            first_name = first_name,
            last_name = last_name,
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
            
        print(f"Pending admin approval...")
        return doctor 
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "phone_number"

    def validate(self, attrs):
        data = super().validate(attrs)

        if self.user.is_blacklisted:
            raise AuthenticationFailed("Блокирани сте и не можете да се најавите додека не ве одблокира админ.")
    
        data.update({
            "user":{
                "id": self.user.id,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "phone_number": self.user.phone_number,
                "role": self.user.role,
            }
        })
        return data