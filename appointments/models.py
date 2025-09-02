from django.db import models
from django.utils import timezone
from datetime import timedelta
from datetime import datetime

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('finished', 'Finished'),
    )

    patient = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                related_name = "appointments"
                                )
    doctor = models.ForeignKey('accounts.Doctor', on_delete=models.CASCADE,
                               related_name='doctor_appointments')
    service = models.ForeignKey('hospitals.Service', on_delete=models.CASCADE)
    department = models.ForeignKey('hospitals.Department', on_delete=models.CASCADE)
    hospital = models.ForeignKey('hospitals.Hospital', on_delete=models.CASCADE)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending')
    is_reccuring = models.BooleanField(default=False)
    reccurence_pattern = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Дневно, неделно, месечно (потребна е потврда од докторот)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time')
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"Пациент {self.patient.first_name} {self.patient.last_name} термин за {self.service.name} кај Доктор {self.doctor.user.first_name} {self.doctor.user.last_name} на дата {self.date} во {self.start_time} часот."

    def can_cancel(self):
        """
        Returns True if appointment can be cancelled (at least 24h before start).
        """
        appointment_datetime = timezone.make_aware(
            datetime.combine(self.date, self.start_time)
        )
        return timezone.now() < appointment_datetime - timedelta(hours=24)
    def requires_confirmation(self):
        """
        Returns True if appointment is recurring and still pending confirmation.
        """
        return self.is_recurring and self.status == "pending"
