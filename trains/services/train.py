from datetime import time
from dataclasses import dataclass
from django.db import transaction
from django.db.models import QuerySet
from dataclasses_json import dataclass_json
from trains.models import Train, Route, Stop, Station, Schedule
from trains.selectors import TrainSelectors, StopSelectors, RouteSelectors, ScheduleSelectors
from trains.serializers import TrainSerializers, RouteSerializers, StopSerializers, ScheduleSerializers


class TrainService:

    class StopOutputModel(Stop):
        station: Station
        class Meta:
            abstract = True

    class RouteOutputModel(Route):
        schedules_of_route: list[Schedule]
        stops_of_route: list['TrainService.StopOutputModel']
        class Meta:
            abstract = True

    class TrainOutputModel(Train):
        routes_of_train: list['TrainService.RouteOutputModel']
        class Meta:
            abstract = True

    class OutputSerializer(TrainSerializers.ModelSerializer):
        class RoutesOfTrainOutputSerializer(RouteSerializers.ModelSerializer):
            stops_of_route = StopSerializers.ModelSerializerWithStation(many=True)
            schedules_of_route = ScheduleSerializers.ModelSerializer(many=True)

        routes_of_train = RoutesOfTrainOutputSerializer(many=True)


    def get_trains_queryset(self) -> QuerySet[Train]:
        train_query_options = TrainSelectors.Options(
            include_deleted=True,
        )
        stop_query_options = StopSelectors.Options(
            include_deleted=True,
        )
        route_query_options = RouteSelectors.Options(
            include_deleted=True,
        )
        schedule_query_options = ScheduleSelectors.Options(
            include_deleted=True,
        )

        trains_queryset = TrainSelectors.get_train_complete_details_queryset(
            query_options=train_query_options,
            stop_query_options=stop_query_options,
            route_query_options=route_query_options,
            schedule_query_options=schedule_query_options,
        )

        return trains_queryset

    @dataclass_json
    @dataclass
    class CreateStopInput:
        order: int
        station: Station
        station_code: str
        distance_kms_from_source: float
        arrival_minutes_from_source: int
        departure_minutes_from_source: int

    @dataclass_json
    @dataclass
    class CreateScheduleInput:
        weekday: str
        arrival_time: time
        departure_time: time
    
    @dataclass_json
    @dataclass
    class CreateRouteInput:
        name: str
        seats: dict
        pricing: dict
        stations: list[Station]
        stops: list['TrainService.CreateStopInput']
        schedules: list['TrainService.CreateScheduleInput']
    
    @dataclass_json
    @dataclass
    class CreateTrainInput:
        name: str
        number: str
        route: 'TrainService.CreateRouteInput'
    
    def create_train(self, data: 'TrainService.CreateTrainInput'):
        with transaction.atomic():
            train = Train.objects.create(
                name=data.name,
                number=data.number,
            )
            route = Route.objects.create(
                train=train,
                name=data.route.name,
                seats=data.route.seats,
                pricing=data.route.pricing,
            )

            bulk_stops = []
            for stop in data.route.stops:
                bulk_stops.append(Stop(
                    route=route,
                    order=stop.order,
                    station=stop.station,
                    distance_kms_from_source=stop.distance_kms_from_source,
                    arrival_minutes_from_source=stop.arrival_minutes_from_source,
                    departure_minutes_from_source=stop.departure_minutes_from_source,
                ))

            Stop.objects.bulk_create(bulk_stops)

            bulk_schedules = []
            for schedule in data.route.schedules:
                bulk_schedules.append(Schedule(
                    route=route,
                    weekday=schedule.weekday,
                    arrival_time=schedule.arrival_time,
                    departure_time=schedule.departure_time,
                ))
            
            Schedule.objects.bulk_create(bulk_schedules)
