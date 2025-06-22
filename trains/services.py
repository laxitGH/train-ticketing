from datetime import date
from dataclasses import dataclass
from bookings.models import Booking
from dataclasses_json import dataclass_json
from trains.models import RouteStation, RouteSchedule
from trains.model_utils import RouteScheduleModelUtils, RouteModelUtils
from trains.serializers import RouteScheduleSerializers, RouteSerializers, RouteStationSerializers
from trains.selectors import RouteScheduleSelectors
from rest_framework import serializers
from utils.queries import QueryUtils


class TrainSearchService:

    @dataclass_json
    @dataclass
    class Input:
        journey_date: date
        source_station_code: str
        destination_station_code: str

    class OutputSerializer(RouteScheduleSerializers.ModelSerializer):
        route = RouteSerializers.ModelSerializerWithTrain()
        source_route_station = RouteStationSerializers.ModelSerializerWithStation()
        destination_route_station = RouteStationSerializers.ModelSerializerWithStation()
        route_stations = RouteStationSerializers.ModelSerializerWithRouteAndStation(many=True)
        seat_availability_data = RouteScheduleSerializers.SeatAvailabilitySerializer()
        booking_windows_data = RouteScheduleSerializers.BookingWindowsSerializer()
        journey_duration_minutes = serializers.IntegerField()
        journey_distance_kms = serializers.FloatField()
        general_pricing = serializers.FloatField()
        tatkal_pricing = serializers.FloatField()

    @staticmethod
    @QueryUtils.log_queries
    def search_trains(input: Input):

        main_filters = dict(route__route_stations_of_route__station__code__in=[input.source_station_code, input.destination_station_code])
        route_schedules = RouteScheduleSelectors.get_schedule_details_queryset(
            journey_date=input.journey_date,
            main_filters=main_filters,
        )

        valid_schedules: list[RouteSchedule] = []

        for schedule in route_schedules:
            route = schedule.route
            stations_of_schedule: list[RouteStation] = getattr(route, 'stations_of_schedule')
            destination_route_station: RouteStation = None
            source_route_station: RouteStation = None

            for route_station in stations_of_schedule:
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
                setattr(schedule, 'destination_route_station',destination_route_station)
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

            journey_duration_minutes = RouteModelUtils.get_total_duration_minutes(
                source_route_station=source_route_station,
                destination_route_station=destination_route_station,
            )
            journey_distance_kms = RouteModelUtils.get_total_distance_kms(
                source_route_station=source_route_station,
                destination_route_station=destination_route_station,
            )
            route_total_distance_kms = RouteModelUtils.get_total_distance_kms(
                route_stations_of_route=stations_of_schedule,
            )

            general_pricing = (journey_distance_kms / route_total_distance_kms) * route.general_price
            tatkal_pricing = (journey_distance_kms / route_total_distance_kms) * route.tatkal_price

            setattr(schedule, 'route_stations', stations_of_schedule)
            setattr(schedule, 'booking_windows_data', booking_windows_data)
            setattr(schedule, 'seat_availability_data', seat_availability_data)
            setattr(schedule, 'journey_duration_minutes',journey_duration_minutes)
            setattr(schedule, 'journey_distance_kms', journey_distance_kms)
            setattr(schedule, 'general_pricing', general_pricing)
            setattr(schedule, 'tatkal_pricing', tatkal_pricing)

        output_serializer = TrainSearchService.OutputSerializer(valid_schedules, many=True)
        return output_serializer.data
