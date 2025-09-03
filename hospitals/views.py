from django.shortcuts import render
from .models import Hospital
from django.http import JsonResponse

def hospitals_data(request):
    hospitals = Hospital.objects.all().prefetch_related("departments")
    data = []
    for hospital in hospitals:
        data.append({
            "id":hospital.id,
            "name":hospital.name,
            "address":hospital.address,
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
# Create your views here.
