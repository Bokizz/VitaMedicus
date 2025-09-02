from django.shortcuts import render,get_object_or_404
from django.http import JsonResponse
from .models import Subscription
from accounts.models import User, Doctor

def subscribe_doctor(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    subscription, created = Subscription.objects.get_or_create(
        patient=request.user,
        doctor=doctor
    )
    if created:
        return JsonResponse({"message": "Subscribed successfully"})
    else:
        return JsonResponse({"message": "Already subscribed"})
# Create your views here.
