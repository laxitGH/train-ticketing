from django.db import models
from django.contrib.auth.models import User
from trains.models import Route, RouteStation, RouteSchedule
from utils.models import ModelUtils


class Booking(ModelUtils.BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, null=False, blank=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    from_route_station = models.ForeignKey(RouteStation, on_delete=models.CASCADE, related_name='from_bookings', null=False, blank=False)
    to_route_station = models.ForeignKey(RouteStation, on_delete=models.CASCADE, related_name='to_bookings', null=False, blank=False)
    route_schedule = models.ForeignKey(RouteSchedule, on_delete=models.CASCADE, null=False, blank=False)
    status = models.CharField(max_length=16, null=False, blank=False)
    seat_number = models.IntegerField(null=True, blank=True)
    