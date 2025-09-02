from django.db import models
from django.conf import settings
from appointments.models import Appointment

class Rating(models.Model):
    appointment = models.OneToOneField(Appointment,
                                       on_delete = models.CASCADE,
                                       related_name="rating")
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"Рецензија за {self.appointment_id}"

class RatingDetail(models.Model):
    ENTITY_CHOICES = [
        ("doctor", "Doctor"),
        ("hospital", "Hospital"),
        ("department","Department"),
    ]

    rating = models.ForeignKey(Rating,
                               on_delete=models.CASCADE,
                               related_name="details",
                            )
    entity_type = models.CharField(max_length = 20, choices = ENTITY_CHOICES)
    entity_id = models.PositiveBigIntegerField()
    score  = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank = True, null = True)
    
    def __str__(self):
        return f"Рецензија за {self.entity_type} со ид ({self.entity_id}) -> {self.score} коментар: {self.comment}"