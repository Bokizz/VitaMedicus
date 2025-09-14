from django.shortcuts import render
from .models import Hospital,Service,Department
from rest_framework import generics
from django.http import JsonResponse
from .serializers import *

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