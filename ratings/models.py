from django.db import models
from django.conf import settings
from appointments.models import Appointment

class Rating(models.Model):
    appointment = models.OneToOneField(Appointment,
                                       on_delete = models.CASCADE,
                                       related_name="rating")
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_ratings",
        null = True,
        blank = True
    )
    hospital = models.ForeignKey(
        "hospitals.Hospital",
        on_delete = models.CASCADE,
        related_name = "hospital_ratings",
        null = True,
        blank = True 
    )
    department = models.ForeignKey(
        "hospitals.Department",
        on_delete = models.CASCADE,
        related_name = "department_ratings",
        null = True,
        blank = True
    )
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Рецензија {self.score} за {self.doctor or self.hospital or self.department}"
# Create your models here.
