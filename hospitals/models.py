import qrcode
from io import BytesIO
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from accounts.models import Doctor

User = get_user_model()

class Hospital(models.Model): # DODAJ GRAD za da se filtrira, trgni qr code stavi samo link do google maps 
    name = models.CharField(max_length = 100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits = 9, 
                                   decimal_places = 6, 
                                   null = True, blank = True)
    longitude = models.DecimalField(max_digits = 9, 
                                    decimal_places=6, 
                                    null = True, blank = True)
    phone_number = models.CharField(max_length = 15, blank  = True)
    link = models.CharField(max_length = 2000,null = True,blank = True, unique = True)
    town = models.CharField(max_length=30,default='NON')
    #rating foreign key

    # qr_code = models.ImageField(upload_to="hospital_qrcodes/", blank = True, null = True)

    # def save(self,*args,**kwargs):
    #     if self.latitude and self.longitude:
    #         maps_url = f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
    #     elif self.address:
    #         maps_url = f"https://www.google.com/maps/search/?api=1&query={self.address}"
    #     else:
    #         maps_url = None
        
    #     if maps_url:
    #         qr = qrcode.make(maps_url)
    #         buffer = BytesIO()
    #         qr.save(buffer, format="PNG")
    #         file_name = f"{self.name}_qr.png"
    #         self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save = False)

        # super().save(*args,**kwargs)
    def __str__(self):
        return self.name
    
    @property
    def doctors(self):
        """Return all doctors working in any department of this hospital."""
        return Doctor.objects.filter(
            department__hospital = self,
            approved = True
        ).select_related('user').distinct()
    
class Department(models.Model):
    hospital = models.ForeignKey(Hospital, 
                            on_delete=models.CASCADE,
                            related_name="departments")
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length = 15, blank = True)

    def __str__(self):
        return f"Одделение за {self.name}, при клиника {self.hospital.name}"
# Create your models here.
    @property
    def doctors(self):
        """"Return all doctors working in this department."""
        return Doctor.objects.filter(
            department_requests__department = self,
            department_requests__approved = True
        ).select_related('user')

class DoctorDepartmentAssignment(models.Model):
    doctor = models.ForeignKey(
        'accounts.Doctor',
        on_delete = models.CASCADE,
        related_name = "department_requests"
    )
    department = models.ForeignKey(
        'hospitals.Department',
        on_delete = models.CASCADE,
        related_name = "doctors_requests"
    )
    approved = models.BooleanField(default = False)
    requested_at = models.DateTimeField(auto_now_add = True)
    approved_at = models.DateTimeField(blank = True, null = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'department'], name='unique_doctor_department')
        ] # da nema duplikat baranja
        verbose_name = "Doctor Department Assignment"
        verbose_name_plural = "Doctor Department Assignments"
    def approve(self):
        """Approve this assignment (irreversible)."""
        if not self.approved:  # only approve if not already approved
            self.approved = True
            from django.utils import timezone
            self.approved_at = timezone.now()
            self.save()
    def __str__(self):
        status = "Approved" if self.approved else "Pending"
        return f"Др. {self.doctor.user.first_name} {self.doctor.user.last_name} бара одобрение за одделението за {self.department.name} ({status})"
    
        
class Service(models.Model):
    name = models.CharField(max_length = 50, unique = True)
    description = models.TextField(blank = True)
    department = models.ForeignKey(Department, 
                                   related_name = 'department_services', 
                                   on_delete=models.CASCADE
                                   )

    def __str__(self):
        return self.name

class DoctorServiceAssignment(models.Model):
    doctor = models.ForeignKey(
        'accounts.Doctor',
        on_delete = models.CASCADE,
        related_name = 'doctor_services'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name = 'service_doctors'
    )
    approved = models.BooleanField(default = False)
    requested_at = models.DateTimeField(auto_now_add = True)
    approved_at = models.DateTimeField(blank = True, null = True)

    available = models.BooleanField(default = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'service'], name='unique_doctor_service')
        ] # da nema duplikat baranja
        verbose_name = "Doctor Service Assignment"
        verbose_name_plural = "Doctor Service Assignments"
    def approve(self):
        """Approve this service (irreversible)."""
        if not self.approved:  # only approve if not already approved
            self.approved = True
            from django.utils import timezone
            self.approved_at = timezone.now()
            self.save()
    
    def __str__(self):
        return f"Др. {self.doctor.user.first_name} {self.doctor.user.last_name} бара одобрение за {self.service.name}"