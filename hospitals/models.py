from django.db import models

class Hospital(models.Model):
    name = models.CharField(max_length = 100)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits = 9, decimal_places = 6, null = True, blank = True)
    longitude = models.DecimalField(max_digits = 9, decimal_places=6, null = True, blank = True)
    phone_number = models.CharField(max_length = 15, blank  = True)

    def __str__(self):
        return self.name
    
class Clinic(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE,related_name="clinics")
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length = 15, blank = True)
    # services = models.ManyToManyField(Service, related_name = "clinics", blank = True)

    def __str__(self):
        return f"Клиника {self.name}, при ({self.hospital.name})"
# Create your models here.
