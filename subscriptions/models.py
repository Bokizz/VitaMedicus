from django.db import models
from django.conf import settings

class Subscription(models.Model):
    doctor = models.ForeignKey('accounts.Doctor', 
                               on_delete=models.CASCADE,
                               related_name='subscribers')
    patient = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name='subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("patient", "doctor")  # prevents duplicate subscriptions

    def __str__(self):
        return f"{self.patient.first_name} {self.patient.last_name} го следи докторот {self.doctor.user.first_name} {self.doctor.user.last_name}"
    
# Create your models here.
