from rest_framework import serializers
from .models import Rating

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = [
            'id',
            'appointment',
            'doctor',
            'hospital',
            'score',
            'comment',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'created_at'
        ]

        def validate(self, data):
            appointment = data.get('appointment')
            if appointment is None:
                raise serializers.ValidationError("Потребен е термин да се внесе.")
            
            if appointment.status != "finished":
                raise serializers.ValidationError("Само извршени термини може да се оценуваат.")
            
            if hasattr(appointment, "rating"):
                raise serializers.ValidationError("Веќе сте го оцениле овој термин.")
            
            return data 
                