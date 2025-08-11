from rest_framework import serializers
from .models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from .models import PhoneVerification

class PatientRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone_number', 'serial_number', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username = validated_data['username'],
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
        print(f"SMS CODE VERIFICATION: Verification code for {user.phone_number}:{code}")

        return user
