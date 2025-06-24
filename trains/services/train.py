from datetime import time
from dataclasses import dataclass
from django.db import transaction
from django.db.models import QuerySet
from dataclasses_json import dataclass_json
from django.core.exceptions import ValidationError
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
        stops: list['TrainService.CreateStopInput']
        schedules: list['TrainService.CreateScheduleInput']
    
    @dataclass_json
    @dataclass
    class CreateTrainInput:
        name: str
        number: str
        route: 'TrainService.CreateRouteInput'
    
    def get_or_create_train(
        self,
        number: str,
        name: str = '',
    ) -> Train:
        train, _ = Train.objects.get_or_create(
            number=number,
            defaults={'name': name},
        )
        return train
    
    def add_routes_to_train(
        self,
        train: Train,
        route_data: 'TrainService.CreateRouteInput',
    ) -> None:
        with transaction.atomic():
            existing_schedules = Schedule.objects.filter(
                route__train=train
            ).select_related('route').values(
                'weekday', 'departure_time', 'arrival_time', 'route__name'
            )

            self.__validate_schedule_conflicts(
                train=train,
                new_schedules=route_data.schedules,
                existing_schedules=existing_schedules,
            )
            
            route = Route.objects.create(
                train=train,
                name=route_data.name,
                seats=route_data.seats,
                pricing=route_data.pricing,
            )

            bulk_stops = []
            for stop in route_data.stops:
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
            for schedule in route_data.schedules:
                bulk_schedules.append(Schedule(
                    route=route,
                    weekday=schedule.weekday,
                    arrival_time=schedule.arrival_time,
                    departure_time=schedule.departure_time,
                ))
            
            Schedule.objects.bulk_create(bulk_schedules)

    def __validate_schedule_conflicts(
        self,
        train: Train,
        new_schedules: list['TrainService.CreateScheduleInput'],
        existing_schedules: QuerySet[Schedule],
    ) -> None:
        existing_by_weekday = {}
        for schedule in existing_schedules:
            weekday = schedule['weekday']
            if weekday not in existing_by_weekday:
                existing_by_weekday[weekday] = []
            existing_by_weekday[weekday].append(schedule)
        
        for new_schedule in new_schedules:
            weekday = new_schedule.weekday
            new_departure = new_schedule.departure_time
            new_arrival = new_schedule.arrival_time
            
            if weekday not in existing_by_weekday:
                continue
            
            for existing in existing_by_weekday[weekday]:
                existing_departure = existing['departure_time']
                existing_arrival = existing['arrival_time']
                if self.__check_schedules_overlap(
                    new_departure, new_arrival,
                    existing_departure, existing_arrival
                ):
                    raise ValidationError(
                        f"Schedule conflict detected for train {train.number} on {weekday}. "
                        f"New schedule ({new_departure}-{new_arrival}) overlaps with "
                        f"existing route '{existing['route__name']}' "
                        f"({existing_departure}-{existing_arrival}). "
                        f"A train can only run one route at a time."
                    )

    def __check_schedules_overlap(
        self,
        start1, end1,
        start2, end2
    ) -> bool:
        def time_to_minutes(time_obj):
            return time_obj.hour * 60 + time_obj.minute
        
        start1_min = time_to_minutes(start1)
        end1_min = time_to_minutes(end1)
        start2_min = time_to_minutes(start2)
        end2_min = time_to_minutes(end2)
        
        if end1_min < start1_min:
            end1_min += 24 * 60
        if end2_min < start2_min:
            end2_min += 24 * 60
        
        return not (end1_min <= start2_min or end2_min <= start1_min)
    
    def remove_route_from_train(
        self,
        route_id: int,
    ) -> None:
        with transaction.atomic():
            route = Route.objects.get(id=route_id)
            route.deleted = True
            route.save()

            stops_of_route: list[Stop] = list(route.stops_of_route.all())
            for stop in stops_of_route:
                stop.deleted = True
                stop.save()

            schedules_of_route: list[Schedule] = list(route.schedules_of_route.all())
            for schedule in schedules_of_route:
                schedule.deleted = True
                schedule.save()
    
    def add_schedule_to_route(
        self,
        train: Train,
        route: Route,
        schedule: 'TrainService.CreateScheduleInput',
    ) -> None:
        with transaction.atomic():
            existing_schedules = Schedule.objects.filter(
                route__train=train
            ).select_related('route').values(
                'weekday', 'departure_time', 'arrival_time', 'route__name'
            )

            self.__validate_schedule_conflicts(
                train=train,
                new_schedules=[schedule],
                existing_schedules=existing_schedules,
            )

            schedule = Schedule.objects.create(
                route_id=route.id,
                weekday=schedule.weekday,
                arrival_time=schedule.arrival_time,
                departure_time=schedule.departure_time,
            )
    
    def remove_schedule_from_route(
        self,
        schedule_id: int,
    ) -> None:
        with transaction.atomic():
            schedule = Schedule.objects.get(id=schedule_id)
            schedule.deleted = True
            schedule.save()

    def update_stops_of_route(
        self,
        route_id: int,
        stops: list['TrainService.CreateStopInput'],
    ) -> None:
        with transaction.atomic():
            route = Route.objects.get(id=route_id)
            stops_of_route: list[Stop] = list(route.stops_of_route.all())
            for stop in stops_of_route:
                stop.deleted = True
                stop.save()

            bulk_stops = []
            for stop in stops:
                bulk_stops.append(Stop(
                    route=route,
                    order=stop.order,
                    station=stop.station,
                    distance_kms_from_source=stop.distance_kms_from_source,
                    arrival_minutes_from_source=stop.arrival_minutes_from_source,
                    departure_minutes_from_source=stop.departure_minutes_from_source,
                ))

            Stop.objects.bulk_create(bulk_stops)

    
