from django.urls import path
from . import views

urlpatterns = [
    path("map/", views.hospitals_map, name="hospitals_map"),
    path("data/", views.hospitals_data, name="hospitals_data"),
]