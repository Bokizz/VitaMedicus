from rest_framework import serializers
from .models import Rating, RatingDetail
from appointments.models import Appointment

class RatingSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField(label = "Термин")

    # doctor
    score_doctor = serializers.IntegerField(required=False, min_value=1, max_value=5)
    comment_doctor = serializers.CharField(required=False, allow_blank=True)

    # hospital
    score_hospital = serializers.IntegerField(required=False, min_value=1, max_value=5)
    comment_hospital = serializers.CharField(required=False, allow_blank=True)

    # department
    score_department = serializers.IntegerField(required=False, min_value=1, max_value=5)
    comment_department = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not (data.get("score_doctor") or data.get("score_hospital") or data.get("score_department")):
            raise serializers.ValidationError("Мора да дадете рецензија на барем една од областите.")

        try:
            appointment = Appointment.objects.get(id=data["appointment_id"])
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Непостоечки термин.")

        if appointment.status != "finished":
            raise serializers.ValidationError("Само извршени термини може да се оценуваат.")

        if hasattr(appointment, "rating"):
            raise serializers.ValidationError("Веќе сте го оцениле овој термин.")

        data["appointment"] = appointment
        return data

    def create(self, validated_data):
        appointment = validated_data["appointment"]
        rating = Rating.objects.create(appointment=appointment)

        details = []
        if validated_data.get("score_doctor") is not None:
            details.append(RatingDetail(
                rating=rating,
                entity_type="doctor",
                entity_id=appointment.doctor.id,
                score=validated_data["score_doctor"],
                comment=validated_data.get("comment_doctor", "")
            ))
        if validated_data.get("score_hospital") is not None:
            details.append(RatingDetail(
                rating=rating,
                entity_type="hospital",
                entity_id=appointment.doctor.hospital.id,
                score=validated_data["score_hospital"],
                comment=validated_data.get("comment_hospital", "")
            ))
        if validated_data.get("score_department") is not None:
            details.append(RatingDetail(
                rating=rating,
                entity_type="department",
                entity_id=appointment.doctor.department.id,
                score=validated_data["score_department"],
                comment=validated_data.get("comment_department", "")
            ))

        RatingDetail.objects.bulk_create(details)
        return rating
class DoctorRatingSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField(label = "Термин")
    score = serializers.IntegerField(min_value = 1, max_value = 5)
    comment = serializers.CharField(required = False, allow_blank = True)

    def validate(self, data):
        try:
            appointment = Appointment.objects.get(id=data["appointment_id"])
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Непостоечки термин.")
        
        if appointment.status != "finished":
            raise serializers.ValidationError("Само извршени термини може да се оценуваат.")

        if hasattr(appointment, "rating"):
            raise serializers.ValidationError("Веќе сте го оцениле овој термин.")

        data["appointment"] = appointment
        return data
    
    def create(self, validated_data):
        appointment = validated_data["appointment"]
        rating = Rating.objects.create(appointment = appointment)

        detail = RatingDetail.objects.create(
            rating = rating,
            entity_type = "doctor",
            entity_id = appointment.doctor.id,
            score = validated_data["score"],
            comment = validated_data.get("comment","")
        )
        return detail
    
    def to_representation(self, instance):
        """Customize response to show detail fields."""
        return {
            "appointment_id": instance.rating.appointment.id,
            "doctor_id": instance.entity_id,
            "score": instance.score,
            "comment": instance.comment,
            "created_at": instance.rating.created_at,
        }