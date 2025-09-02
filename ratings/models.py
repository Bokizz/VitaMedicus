from django.db import models
from django.conf import settings
from appointments.models import Appointment
from django.contrib.contenttypes.models import ContentType

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
    
    def entity_name(self):
        """Return the actual entity name instead of raw ID"""
        model_map = {
            "doctor": "Doctor",
            "hospital": "Hospital",
            "department": "Department",
        }
        model_name = model_map.get(self.entity_type.lower())
        if not model_name:
            return f"Unknown ({self.entity_type}:{self.entity_id})"

        try:
            Model = ContentType.objects.get(model=model_name.lower()).model_class()
            obj = Model.objects.get(id=self.entity_id)
            return str(obj)
        except Exception:
            return f"{model_name} #{self.entity_id}"
    
    def __str__(self):
        return f"Рецензија за {self.entity_type} со ид ({self.entity_id}) -> {self.score} коментар: {self.comment}"