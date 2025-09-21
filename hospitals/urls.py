from django.urls import path
from .views import *

urlpatterns = [
    path("map/", hospitals_map, name="hospitals_map"),
    path("data/", hospitals_data, name="hospitals_data"),

    path("hospitals/", HospitalListView.as_view(), name="hospital-list"),
    path("hospitals/<int:hospital_id>/departments/", HospitalDepartmentsListView.as_view(), name="hospital-departments"),
    path("hospitals/<int:hospital_id>/doctors/<int:user_id>/", HospitalDoctorsView.as_view(), name="hospital-doctors"),

    path("departments/", DepartmentListView.as_view(), name="department-list"),
    path("departments/<int:department_id>/doctors/", DepartmentDoctorsView.as_view(), name="department-doctors"),
    path("departments/<int:department_id>/services/", DepartmentServicesListView.as_view(), name="department-services"),

    path("services/", ServiceListView.as_view(), name="service-list"),
    path("service/",service_page, name="book-service"),
    path("service/<int:doctor_id>/services/", DoctorServicesView.as_view(), name="doctor-services"),
]