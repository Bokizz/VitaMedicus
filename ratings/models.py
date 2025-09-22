from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Rating(models.Model):
    doctor = models.ForeignKey(
        'accounts.Doctor',
        on_delete = models.CASCADE,
        related_name = "doc_ratings"
    )
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete = models.CASCADE,
        related_name = "hospital_ratings"
    )
    doctor_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    hospital_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(
        blank=True,
        help_text="Анонимен коментар и рецензија за нивниот термин"
    )
    is_anonymous = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Рецензија за Докторот: {self.doctor_rating}, Клиниката: {self.hospital_rating}"