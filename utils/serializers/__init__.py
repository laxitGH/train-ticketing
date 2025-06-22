from datetime import timedelta
from rest_framework import serializers
from django.utils import timezone


class JourneyDateSerializer(serializers.DateField):
    format = '%Y-%m-%d'

    def validate(self, value):
        today = timezone.now().date()
        max_date = today + timedelta(days=120)
        if value < today or value > max_date:
            raise serializers.ValidationError("Date cannot be in the past or more than 120 days from today")
        return value
