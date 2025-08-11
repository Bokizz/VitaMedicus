from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    ]

    phone_number = models.CharField(max_length = 12, unique = True)
    serial_number = models.CharField(max_length = 13, unique = True)
    role = models.CharField(max_length = 10, choices = ROLE_CHOICES)
    is_phone_verified = models.BooleanField(default = False)

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class PhoneVerification(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    code = models.CharField(max_length = 6)
    created_at = models.DateTimeField(auto_now_add = True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default = False)

    def __str__(self):
        return f"Verification for {self.user.phone_number}"
# Create your models here.
