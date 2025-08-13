from rest_framework import serializers
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from .models import PhoneVerification, User
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

# class DoctorRegistrationSerializer(serializers.ModelSerializer):
#     hospital_id = serializers.IntegerField(required = False, allow_null = True)
#     clinic_id = serializers.IntegerField(required = False, allow_null = True)
#     specialization = serializers.IntegerField(max_length = 50,required = False, allow_blank = True)

#     class Meta:
#         model = User
#         fields = ['first_name', 'last_name', 'phone_number','serial_number',
#                   'password','hospital_id','clinic_id','specialization']
#         extra_kwargs = {
#             'password':{'write_only': True}
#         }

#         def create(self, validated_data):
#             hospital_id = validated_data.pop('hospital_id', None)
#             clinic_id = validated_data.pop('clinic_id', None)
#             specialization = validated_data.pop('specialization','')

#             user = User.objects.create_user(
#                 first_name = validated_data['first_name'],
#                 last_name = validated_data['last_name'],
#                 phone_number = validated_data['phone_number'],
#                 serial_number = validated_data['serial_number'],
#                 password = validated_data['password'],
#                 role = 'doctor',
#                 is_active = True
#             )

#             DoctorProfile.objects.create(
#                 user = user,
#                 hospital_id = hospital_id,
#                 clinic_id = clinic_id,
#                 specialization = specialization,
#                 is_approved = False
#             )

#             code = get_random_string(6,allowed_chars = '0123456789')
#             PhoneVerification.objects.create(
#                 user = user,
#                 coed = code,
#                 created_at = timezone.now(),
#                 expires_at = timezone.now() + timedelta(minutes=15)
#             )
#             print