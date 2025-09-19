from rest_framework import serializers
from .models import Appointment
from hospitals.models import Service

class AppointmentSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.user.get_full_name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "doctor", "doctor_name", "service", "service_name",
            "date", "start_time", "end_time", "booked", "status"
        ]

class AvailableTimeSlotSerializer(serializers.Serializer):
    time = serializers.TimeField(format='%H:%M')
    available = serializers.BooleanField()