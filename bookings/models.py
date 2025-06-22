from django.db import models
from django.contrib.auth.models import User
from trains.models import Stop, Schedule
from utils.models import ModelUtils


class Booking(ModelUtils.BaseModel):
    journey_date = models.DateField(null=False, blank=False)
    user = models.ForeignKey(User, related_name='bookings_of_user', on_delete=models.CASCADE, null=False, blank=False)
    schedule = models.ForeignKey(Schedule, related_name='bookings_of_schedule', on_delete=models.CASCADE, null=False, blank=False)
    from_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='bookings_of_from_stop', null=False, blank=False)
    to_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='bookings_of_to_stop', null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    cancellation_datetime = models.DateTimeField(null=True, blank=True)
    confirmation_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, null=False, blank=False)
    type = models.CharField(max_length=16, null=False, blank=False)
    