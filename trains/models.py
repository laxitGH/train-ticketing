from django.db import models
from django.utils import timezone
from utils.models import ModelUtils
from django.db.models import QuerySet
from datetime import date, datetime, timedelta
from trains.dataclasses import RouteScheduleBookingWindowsData


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

    def get_ordered_route_stations(self, reverse: bool = False) -> QuerySet['RouteStation']:
        return self.route_stations_of_route.order_by('order' if not reverse else '-order')
    
    @property
    def tatkal_price(self) -> float:
        return float(self.pricing.get('tatkal', 0))
    
    @property
    def general_price(self) -> float:
        return float(self.pricing.get('general', 0))
    
    @property
    def total_seats(self) -> int:
        return sum(self.seats.values())
    
    @property
    def tatkal_seats(self) -> int:
        return self.seats.get('tatkal', 0)
    
    @property
    def general_seats(self) -> int:
        return self.seats.get('general', 0)
    
    @property
    def source_station(self) -> 'RouteStation':
        return self.get_ordered_route_stations().first()
    
    @property 
    def destination_station(self) -> 'RouteStation':
        return self.get_ordered_route_stations().last()

    @property
    def total_distance_kms(self) -> float:
        return self.get_ordered_route_stations().last().distance_kms_from_source
    
    @property
    def total_duration_minutes(self) -> int:
        return self.get_ordered_route_stations().last().arrival_minutes_from_source
    
    def __str__(self) -> str:
        return f"[{self.id}] {self.name} \t USING TRAIN [{self.train.number}] {self.train.name}"


class RouteStation(ModelUtils.BaseModel):
    order = models.PositiveIntegerField(null=False, blank=False)
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_stations_of_route', null=False, blank=False)
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='route_stations_of_station', null=False, blank=False)
    departure_minutes_from_source = models.IntegerField(null=False, blank=False) 
    arrival_minutes_from_source = models.IntegerField(null=False, blank=False)
    distance_kms_from_source = models.FloatField(null=False, blank=False)

    class Meta:
        unique_together = ['route', 'order']
        ordering = ['route', 'order']
    
    def __str__(self) -> str:
        return f"STOP [{self.order}] {self.station.code} \t ON ROUTE [{self.route.id}] {self.route.name}"
    

class RouteSchedule(ModelUtils.BaseModel):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules_of_route', null=False, blank=False)
    weekday = models.CharField(max_length=3, null=False, blank=False)
    departure_time = models.TimeField(null=False, blank=False)
    arrival_time = models.TimeField(null=False, blank=False)

    def get_booking_windows_data(self, journey_date: date) -> RouteScheduleBookingWindowsData:
        now = timezone.now()
        departure_datetime = datetime.combine(journey_date, self.departure_time)
        
        general_booking_opening_datetime = departure_datetime - timedelta(days=120)
        general_booking_closing_datetime = departure_datetime - timedelta(hours=4)
        
        tatkal_booking_opening_datetime = departure_datetime - timedelta(hours=2)
        tatkal_booking_closing_datetime = departure_datetime - timedelta(hours=2, minutes=-10)
        
        return RouteScheduleBookingWindowsData(
            tatkal_booking_opening_datetime=tatkal_booking_opening_datetime,
            tatkal_booking_closing_datetime=tatkal_booking_closing_datetime,
            general_booking_opening_datetime=general_booking_opening_datetime,
            general_booking_closing_datetime=general_booking_closing_datetime,
            general_booking_open=general_booking_opening_datetime <= now <= general_booking_closing_datetime,
            tatkal_booking_open=tatkal_booking_opening_datetime <= now <= tatkal_booking_closing_datetime,
        )
    
    def get_seat_availability_data(self):
        pass

    def __str__(self):
        return f"Schedule {self.id} - {self.route.name} - {self.weekday} {self.departure_time}"