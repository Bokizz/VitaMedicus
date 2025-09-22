from django.urls import path
from .views import *

urlpatterns = [
    path('rate/<int:appointment_id>/', rate_doctor_hospital_page, name='rate'),
    path('doctor/ratings/', doctor_ratings, name='doctor-ratings'),
    path('hospital/ratings/', hospital_ratings, name='hospital-ratings'),
    path('search-ratings/', search_ratings, name='search-ratings'),
    path('ratings/<str:item_type>/<int:item_id>/', view_public_ratings, name='public-ratings'),

]