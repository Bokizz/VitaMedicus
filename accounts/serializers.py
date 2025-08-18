from rest_framework import serializers
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
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
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(max_length = 12)
    serial_number = serializers.CharField(max_length = 13)
    password = serializers.CharField(write_only = True)

    specialization = serializers.ChoiceField(
        choices = Doctor._meta.get_field('specialization').choices
    )
    hospital = serializers.PrimaryKeyRelatedField(
        queryset = Hospital.objects.all()
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset = Department.objects.all()
    )

    class Meta:
        model = Doctor
        fields = ['first_name', 'last_name', 'phone_number','serial_number',
                  'password','specialization','hospital','department']

        def create(self, validated_data):
            first_name = validated_data.pop("first_name")
            last_name = validated_data.pop("last_name")
            phone_number = validated_data.pop("phone_number")
            serial_number = validated_data.pop("phone_number")
            password = validated_data.pop("password")
            hospital = validated_data.pop("hospital")
            department = validated_data.pop("department")

            user = User.objects.create_user(
                first_name = first_name,
                last_name = last_name,
                phone_number = phone_number,
                serial_number =  serial_number,
                password = password,
                role = 'doctor',
                is_active = True
            )
            user.set_password(password)
            user.save()

            doctor = Doctor.objects.create(
                user = user,
                specialization = specialization,
                is_approved = False
            )
            doctor.hospital.add(hospital)
            doctor.save()

            DoctorDepartmentAssignment.objects.create(
                doctor = doctor,
                department = department,
                approved = False
            )
            
            print(f"Pending admin approval...")
            return doctor 
