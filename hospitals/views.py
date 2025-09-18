from django.shortcuts import render
from .models import *
from rest_framework import generics
from django.http import JsonResponse
from .serializers import *

def service_page(request):
     # Get doctor_id and department_id from query parameters or session
    doctor_id = request.GET.get('doctor_id') or request.session.get('doctor_id')
    department_id = request.GET.get('department_id') or request.session.get('department_id')
    
    if not doctor_id or not department_id:
        # Handle missing parameters - redirect or show error
        return render(request, 'service.html', {
            'error': 'Доктор или одделение не се специфицирани'
        })
    
    # Get doctor and department objects
    doctor = get_object_or_404(Doctor, id=doctor_id, authorized=True)
    department = get_object_or_404(Department, id=department_id)
    
    # Store in session for potential future use
    request.session['doctor_id'] = doctor_id
    request.session['department_id'] = department_id
    
    # Get services for this doctor in the specified department
    services_assignments = DoctorServiceAssignment.objects.filter(
        doctor_id=doctor_id,
        approved=True,
        available=True,
        service__department_id=department_id
    ).select_related('service')
    
    # Format the services data
    services = []
    for assignment in services_assignments:
        services.append({
            'id': assignment.service.id,
            'name': assignment.service.name,
            'description': assignment.service.description,
        })
    
    context = {
        'doctor': {
            'id': doctor.id,
            'name': f"Д-р {doctor.user.first_name} {doctor.user.last_name}"
        },
        'department': {
            'id': department.id,
            'name': department.name
        },
        'services': services
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

class DoctorServicesView(generics.ListAPIView):
    serializer_class = DoctorServicesSerializer

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        department_id = self.kwargs.get('department_id')
        
        if not doctor_id:
            return DoctorServiceAssignment.objects.none()
        
        queryset = DoctorServiceAssignment.objects.filter(
            doctor_id=doctor_id,
            approved=True,
            available=True,
            doctor__authorized=True,
            doctor__user__is_blacklisted=False
        ).select_related('service')

        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response({
                "detail": "No services found for this doctor",
                "doctor_id": self.kwargs.get('doctor_id'),
                "department_id": self.kwargs.get('department_id')
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)