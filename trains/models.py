from django.db import models
from utils.enums import BookingType
from utils.models import ModelUtils


class Station(ModelUtils.BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False)
    city = models.CharField(max_length=256, null=False, blank=False)
    state = models.CharField(max_length=256, null=False, blank=False)
    code = models.CharField(max_length=16, unique=True, null=False, blank=False)
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.name}"


class Train(ModelUtils.BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False)
    number = models.CharField(max_length=16, unique=True, null=False, blank=False)
    
    def __str__(self) -> str:
        return f"[{self.number}] {self.name}"


class Route(ModelUtils.BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False)
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='routes_of_train', null=False, blank=False)
    pricing = models.JSONField(default=dict, null=False, blank=False)
    seats = models.JSONField(default=dict, null=False, blank=False)
    
    @property
    def tatkal_price(self) -> float:
        return float(self.pricing.get(BookingType.TATKAL.value, 0))
    
    @property
    def general_price(self) -> float:
        return float(self.pricing.get(BookingType.GENERAL.value, 0))
    
    @property
    def total_seats(self) -> int:
        return sum(self.seats.values())
    
    @property
    def tatkal_seats(self) -> int:
        return self.seats.get(BookingType.TATKAL.value, 0)
    
    @property
    def general_seats(self) -> int:
        return self.seats.get(BookingType.GENERAL.value, 0)
    
    def __str__(self) -> str:
        return f"[{self.id}] {self.name}"


class Stop(ModelUtils.BaseModel):
    order = models.PositiveIntegerField(null=False, blank=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops_of_route', null=False, blank=False)
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='stops_of_station', null=False, blank=False)
    departure_minutes_from_source = models.IntegerField(null=False, blank=False) 
    arrival_minutes_from_source = models.IntegerField(null=False, blank=False)
    distance_kms_from_source = models.FloatField(null=False, blank=False)

    @property
    def stoppage_duration_minutes(self) -> int:
        return self.arrival_minutes_from_source - self.departure_minutes_from_source

    class Meta:
        unique_together = ['route', 'order']
        ordering = ['route', 'order']
    
    def __str__(self) -> str:
        return f"[{self.id}] {self.station.code} \t ON ROUTE [{self.route.id}]"
    

class Schedule(ModelUtils.BaseModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules_of_route', null=False, blank=False)
    weekday = models.CharField(max_length=3, null=False, blank=False)
    departure_time = models.TimeField(null=False, blank=False)
    arrival_time = models.TimeField(null=False, blank=False)

    def __str__(self):
        return f"{self.weekday} [{self.id}] \t ON ROUTE [{self.route.id}]"