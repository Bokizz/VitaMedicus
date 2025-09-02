from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import render
from .models import *
from .serializers import *
from accounts.permissions import NotBlacklisted

class DoctorRatingCreateView(generics.CreateAPIView):
    serializer_class = DoctorRatingSerializer
    permission_classes = [NotBlacklisted] # permissions.isAuthenticated dodaj posle test

# Create your views here.
