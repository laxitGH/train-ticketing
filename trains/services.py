from datetime import date
from dataclasses import dataclass
from bookings.models import Booking
from django.db.models import Prefetch
from dataclasses_json import dataclass_json
from trains.models import RouteStation, RouteSchedule
from trains.model_utils import RouteScheduleModelUtils, RouteUtils
from trains.serializers import TrainSearchOutputSerializer
from utils.queries import QueryUtils


class TrainSearchService:

    @dataclass_json
    @dataclass
    class Input:
        journey_date: date
        source_station_code: str
        destination_station_code: str

    @staticmethod
    @QueryUtils.log_queries
    def search_trains(input: Input):
        weekday = input.journey_date.strftime('%a').upper()[:3]
        
        route_schedules = RouteSchedule.objects.filter(
            weekday=weekday,
            route__route_stations_of_route__station__code__in=[input.source_station_code, input.destination_station_code]
        ).select_related('route__train').prefetch_related(
            Prefetch(
                'route__route_stations_of_route',
                queryset=RouteStation.objects.select_related('station').order_by('order'),
                to_attr='stations_of_schedule'
            ),
            Prefetch(
                'bookings_of_route_schedule',
                queryset=Booking.objects.filter(journey_date=input.journey_date).select_related('user'),
                to_attr='bookings_of_schedule'
            )
        ).distinct()

        valid_schedules: list[RouteSchedule] = []
        
        for schedule in route_schedules:
            route = schedule.route
            print(f'schedule: {schedule} | for route: {route}')
            
            stations_of_schedule: list[RouteStation] = getattr(route, 'stations_of_schedule')
            destination_route_station: RouteStation = None
            source_route_station: RouteStation = None
            
            for route_station in stations_of_schedule:
                print(f'route_station: {route_station}')
                if route_station.station.code == input.source_station_code:
                    source_route_station = route_station
                elif route_station.station.code == input.destination_station_code:
                    destination_route_station = route_station
            
            if (
                source_route_station and 
                destination_route_station and 
                source_route_station.order < destination_route_station.order
            ):
                setattr(schedule, 'source_route_station', source_route_station)
                setattr(schedule, 'destination_route_station', destination_route_station)
                print(f"✅ Valid schedule: {schedule}")
                valid_schedules.append(schedule)

        for schedule in valid_schedules:
            route = schedule.route
            source_route_station: RouteStation = getattr(schedule, 'source_route_station')
            destination_route_station: RouteStation = getattr(schedule, 'destination_route_station')
            bookings_of_schedule: list[Booking] = getattr(schedule, 'bookings_of_schedule', [])
            stations_of_schedule: list[RouteStation] = getattr(route, 'stations_of_schedule')
            
            booking_windows_data = RouteScheduleModelUtils.get_booking_windows_data(
                journey_date=input.journey_date,
                schedule=schedule,
            )
            seat_availability_data = RouteScheduleModelUtils.get_seat_availability_data(
                journey_date=input.journey_date,
                bookings=bookings_of_schedule,
                schedule=schedule,
            )

            journey_duration_minutes = RouteUtils.get_total_duration_minutes(
                source_route_station=source_route_station,
                destination_route_station=destination_route_station,
            )
            journey_distance_kms = RouteUtils.get_total_distance_kms(
                source_route_station=source_route_station,
                destination_route_station=destination_route_station,
            )
            route_total_distance_kms = RouteUtils.get_total_distance_kms(
                route_stations_of_route=stations_of_schedule,
            )

            general_pricing = (journey_distance_kms / route_total_distance_kms) * route.general_price
            tatkal_pricing = (journey_distance_kms / route_total_distance_kms) * route.tatkal_price
            
            setattr(schedule, 'route_stations', stations_of_schedule)
            setattr(schedule, 'booking_windows_data', booking_windows_data)
            setattr(schedule, 'seat_availability_data', seat_availability_data)
            setattr(schedule, 'journey_duration_minutes', journey_duration_minutes)
            setattr(schedule, 'journey_distance_kms', journey_distance_kms)
            setattr(schedule, 'general_pricing', general_pricing)
            setattr(schedule, 'tatkal_pricing', tatkal_pricing)
            
        output_serializer = TrainSearchOutputSerializer(valid_schedules, many=True)
        print(f"🎯 Found {len(valid_schedules)} valid train schedules")
        return output_serializer.data
