from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password = None, **extra_fields):
        if not phone_number:
            raise ValueError("Мора да е внесен телефонскиот број!")
        user = self.model(phone_number = phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role','admin')
        return self.create_user(phone_number, password, **extra_fields)

    
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
    ]

    first_name = models.CharField(max_length = 15, blank = True)
    last_name = models.CharField(max_length = 30, blank = True)
    email = models.CharField(max_length = 50, unique = True, blank = True, null = True)
    phone_regex = RegexValidator(regex = r'^\+3897\d{7}$', message = "Телефонскиот број треба да е од формат +3897XXXXXXX")
    phone_number = models.CharField(validators = [phone_regex],max_length = 12, unique = True)
    serial_number = models.CharField(max_length = 13, unique = True)
    role = models.CharField(max_length = 10, choices = ROLE_CHOICES)
    
    is_phone_verified = models.BooleanField(default = False)
    is_active = models.BooleanField(default = True)
    is_staff = models.BooleanField(default = False)

    is_blacklisted = models.BooleanField(default = False)
    date_joined = models.DateTimeField(default=timezone.now())
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone_number
    
class PhoneVerification(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    code = models.CharField(max_length = 6)
    created_at = models.DateTimeField(auto_now_add = True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default = False)

    def __str__(self):
        return f"Verification for {self.user.phone_number}"
# Create your models here.

class Doctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, 
                                on_delete=models.CASCADE,
                                related_name = 'doctor',
                                limit_choices_to={'role':'doctor'}
                                )
    hospital = models.ForeignKey('hospitals.Hospital', 
                                related_name = 'hospital_doctors',
                                blank = True,
                                on_delete=models.SET_NULL,
                                null = True
                                )
    authorized = models.BooleanField(default = False)
    specialization = models.CharField(max_length = 50, blank = True,
                                      choices = [
        ("cardiology", "Кардиологија"),
        ("neurology", "Неврологија"),
        ("pediatrics", "Педијатрија"),
        ("orthopedics", "Ортопедија"),
        ("psychiatry", "Психијатрија"),
    ])
    #rating foreign key

    def __str__(self):
        return f"Доктор: {self.user.first_name} {self.user.last_name}, специјализација:{self.specialization or 'NON'}"
    
    @property
    def approved_departments(self):
        from hospitals.models import Department
        """Departments where this doctor is approved."""
        return Department.objects.filter(
            doctors_requests__doctor = self,
            doctors_requests__approved = True
        )
    
    @property
    def pending_department_requests(self):
        from hospitals.models import Department
        """Departments where the doctor has requested but is not yet approved."""
        return Department.objects.filter(
            doctors_requests__doctor = self,
            doctors_requests__approved = False
        )


class PasswordResetToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        if self.created_at >= timezone.now() - timedelta(hours=1):  # 1 hour expiry
            return False
        else:
            return True