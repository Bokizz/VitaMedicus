from rest_framework import generics, permissions
from django.shortcuts import render
from .models import Rating
from .serializers import RatingSerializer
from accounts.permissions import NotBlacklisted

class RatingCreateView(generics.CreateAPIView):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated,NotBlacklisted]

    def perform_create(self, serializer):
        # Ensure rating is linked properly but patient info is not stored
        serializer.save()
# Create your views here.
