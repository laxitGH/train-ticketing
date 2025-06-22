from django.db import models
from django.contrib.auth.models import User
from trains.models import Route, RouteStation, RouteSchedule
from utils.models import ModelUtils


class Booking(ModelUtils.BaseModel):
    journey_date = models.DateField(null=False, blank=False)
    user = models.ForeignKey(User, related_name='bookings_of_user', on_delete=models.CASCADE, null=False, blank=False)
    route = models.ForeignKey(Route, related_name='bookings_of_route', on_delete=models.CASCADE, null=False, blank=False)
    route_schedule = models.ForeignKey(RouteSchedule, related_name='bookings_of_route_schedule', on_delete=models.CASCADE, null=False, blank=False)
    from_route_station = models.ForeignKey(RouteStation, on_delete=models.CASCADE, related_name='from_bookings_of_route_station', null=False, blank=False)
    to_route_station = models.ForeignKey(RouteStation, on_delete=models.CASCADE, related_name='to_bookings_of_route_station', null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    cancellation_datetime = models.DateTimeField(null=True, blank=True)
    confirmation_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, null=False, blank=False)
    type = models.CharField(max_length=16, null=False, blank=False)
    