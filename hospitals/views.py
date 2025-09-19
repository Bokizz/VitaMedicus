from django.shortcuts import render,redirect
from .models import *
from rest_framework import generics
from django.http import JsonResponse
from .serializers import *
from django.shortcuts import get_object_or_404
from accounts.models import Doctor
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView


def service_page(request):
     # Get doctor_id and department_id from query parameters or session
    doctor_id = request.GET.get('doctor_id') or request.session.get('doctor_id')
    department_id = request.GET.get('department_id') or request.session.get('department_id')
    if not doctor_id or not department_id:
        return Response("NEMA DOKTOR ID ILI DEPARTMENT ID")
    
    doctor_id = int(doctor_id)
    department_id = int(department_id)

    # Store in session for potential future use
    request.session['doctor_id'] = doctor_id
    request.session['department_id'] = department_id
    doctor = Doctor.objects.select_related(
            'user', 
            'hospital'
        ).filter(
            id=doctor_id,
            authorized=True,
            user__is_active=True,
            user__is_blacklisted=False
        ).first()
    department = get_object_or_404(Department, id=department_id)    
    context = {
        'doctor': {
            'id': doctor.id,
            'name': f"Д-р {doctor.user.first_name} {doctor.user.last_name}"
        },
        'department': {
            'id': department.id,
            'name': department.name
        }
    }
    return render(request,"services/service.html",context)

def hospitals_data(request):
    hospitals = Hospital.objects.all().prefetch_related("departments")
    data = []
    for hospital in hospitals:
        data.append({
            "id":hospital.id,
            "name":hospital.name,
            "address":hospital.address,
            "town":hospital.town,
            "latitude":float(hospital.latitude) if hospital.latitude else None, 
            "longitude":float(hospital.longitude) if hospital.longitude else None,
            "departments": [
                {"id": d.id, "name":d.name,"phone_number":d.phone_number}
                for d in hospital.departments.all()
            ]
        })
    return JsonResponse(data, safe=False)

def hospitals_map(request):
    return render(request, "hospitals/map.html")

class HospitalListView(generics.ListAPIView):
    queryset = Hospital.objects.all()
    serializer_class = HospitalSerializer

class HospitalDoctorsView(generics.ListAPIView):
    serializer_class = DoctorSerializer

    def get_queryset(self):
        hospital_id = self.kwargs['hospital_id']
        
        # Only show authorized doctors from this specific hospital
        return Doctor.objects.filter(
            hospital_id=hospital_id,
            authorized=True,
            user__is_active=True,
            user__is_blacklisted=False
        )

class DepartmentListView(generics.ListAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        hospital_id = self.request.query_params.get("hospital")
        qs = Department.objects.all()
        if hospital_id:
            qs = qs.filter(hospital_id=hospital_id)
        return qs

class HospitalDepartmentsListView(generics.ListAPIView):
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        hospital_id = self.kwargs.get("hospital_id")
        return Department.objects.filter(hospital_id=hospital_id)

class ServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        department_id = self.request.query_params.get("department")
        qs = Service.objects.all()
        if department_id:
            qs = qs.filter(department_id=department_id)
        return qs
    
    
class DepartmentServicesListView(generics.ListAPIView):
    serializer_class = ServiceSerializer

    def get_queryset(self):
        department_id = self.kwargs.get("department_id")
        return Service.objects.filter(department_id=department_id)


class DepartmentDoctorsView(generics.ListAPIView):
    serializer_class = DepartmentDoctorSerializer

    def get_queryset(self):
        department_id = self.request.query_params.get("department")
        
        if not department_id:
            return DoctorDepartmentAssignment.objects.none()
        
        # Get only approved assignments for the selected department
        queryset = DoctorDepartmentAssignment.objects.filter(
            department_id=department_id,
            approved=True,
            doctor__authorized=True,
            doctor__user__is_blacklisted=False
        ).select_related(
            'doctor',
            'doctor__user',
            'doctor__hospital',
            'department'
        )
        
        return queryset

class DoctorServicesView(APIView):
    def get(self, request, doctor_id):
        department_id = request.GET.get('department_id') or request.session.get('department_id')
        
        if not department_id:
            return Response({
                "error": "Department ID is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get approved services for this doctor in the specified department
            services_assignments = DoctorServiceAssignment.objects.filter(
                doctor_id=doctor_id,
                approved=True,
                available=True,
                service__department_id=department_id
            ).select_related('service')
            
            # Format the response
            services = []
            for assignment in services_assignments:
                services.append({
                    'id': assignment.service.id,
                    'name': assignment.service.name,
                    'description': assignment.service.description,
                })
            
            return Response({
                'services': services,
                'doctor_id': doctor_id,
                'department_id': department_id
            })
        
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)