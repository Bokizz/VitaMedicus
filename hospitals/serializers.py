from rest_framework import serializers
from .models import *
from accounts.models import Doctor

class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['id', 'name','town','address']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'hospital']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name','description']

class DoctorSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    department_id = serializers.SerializerMethodField()
    
    def get_department_id(self, obj):
        # Get the first approved department assignment
        assignment = obj.department_requests.filter(approved=True).first()
        return assignment.department.id if assignment else None

    class Meta:
        model = Doctor
        fields = [
            'id',
            'first_name',
            'last_name', 
            'hospital_name',
            'department_id'
        ]

        
class DepartmentDoctorSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    first_name = serializers.CharField(source='doctor.user.first_name', read_only=True)
    last_name = serializers.CharField(source='doctor.user.last_name', read_only=True)
    
    hospital_name = serializers.CharField(source='doctor.hospital.name', read_only=True)
    
    class Meta:
        model = DoctorDepartmentAssignment
        fields = [
            'doctor_id',
            'first_name',
            'last_name',
            'hospital_name',
            'approved',
            'approved_at'
        ]

class DoctorServicesSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    service_details = ServiceSerializer(source='service',read_only=True)
    class Meta:
        model = DoctorServiceAssignment
        fields = [
            'doctor_id',
            'service_details',
            'available',
            'approved',
        ]
