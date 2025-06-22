from datetime import date
from dataclasses import dataclass
from bookings.models import Booking
from dataclasses_json import dataclass_json
from trains.models import RouteStation, RouteSchedule
from trains.model_utils import RouteScheduleModelUtils, RouteModelUtils, RouteScheduleBookingWindowsData, RouteScheduleSeatAvailabilityData 
from trains.selectors import RouteScheduleSelectors
from utils.enums import BookingType


class TrainSearchService:

    @dataclass_json
    @dataclass
    class Input:
        journey_date: date
        source_station_code: str
        destination_station_code: str        

    @staticmethod
    def search_trains(input: Input) -> list[RouteSchedule]:
        main_filters = dict(
            route__route_stations_of_route__station__code__in=[input.source_station_code, input.destination_station_code],
        )
        route_schedules_queryset = RouteScheduleSelectors.get_schedule_details_queryset(
            journey_date=input.journey_date,
            main_filters=main_filters,
        )

        valid_schedules: list[RouteSchedule] = []
        for schedule in route_schedules_queryset:
            route = schedule.route
            bookings_of_route_schedule: list[Booking] = list(schedule.bookings_of_route_schedule.all())
            route_stations_of_route: list[RouteStation] = list(route.route_stations_of_route.all())
            destination_route_station: RouteStation = None
            source_route_station: RouteStation = None

            for route_station in route_stations_of_route:
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
            bookings_of_route_schedule: list[Booking] = list(schedule.bookings_of_route_schedule.all())
            route_stations_of_route: list[RouteStation] = list(route.route_stations_of_route.all())

            booking_windows_data = RouteScheduleModelUtils.get_booking_windows_data(
                schedule=schedule,
                journey_date=input.journey_date,
                source_route_station=source_route_station,
            )
            seat_availability_data = RouteScheduleModelUtils.get_seat_availability_data(
                schedule=schedule,
                bookings=bookings_of_route_schedule,
                journey_date=input.journey_date,
                source_route_station=source_route_station,
                destination_route_station=destination_route_station,
                route_stations_of_route=route_stations_of_route,
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
                route_stations_of_route=route_stations_of_route,
            )

            general_pricing = (journey_distance_kms / route_total_distance_kms) * route.general_price
            tatkal_pricing = (journey_distance_kms / route_total_distance_kms) * route.tatkal_price

            setattr(schedule, 'route_stations', route_stations_of_route)
            setattr(schedule, 'booking_windows_data', booking_windows_data)
            setattr(schedule, 'seat_availability_data', seat_availability_data)
            setattr(schedule, 'journey_duration_minutes',journey_duration_minutes)
            setattr(schedule, 'journey_distance_kms', journey_distance_kms)
            setattr(schedule, 'general_pricing', general_pricing)
            setattr(schedule, 'tatkal_pricing', tatkal_pricing)

        return valid_schedules


class TrainAvailabilityStatusService:

    @dataclass_json
    @dataclass
    class Input:
        schedule_id: int
        journey_date: date
        booking_type: BookingType
        destination_station_code: str
        source_station_code: str

    @dataclass_json
    @dataclass
    class Output:
        booking_windows_data: RouteScheduleBookingWindowsData
        seat_availability_data: RouteScheduleSeatAvailabilityData
        destination_route_station: RouteStation
        source_route_station: RouteStation

    @staticmethod
    def get_seat_availability(input: Input):
        main_filters = dict(id=input.schedule_id)
        route_schedules_queryset = RouteScheduleSelectors.get_schedule_details_queryset(
            journey_date=input.journey_date,
            main_filters=main_filters,
        )

        route_schedule = route_schedules_queryset.first()
        if not route_schedule:
            raise ValueError('Schedule not found')
        
        route = route_schedule.route
        source_route_station = None    
        destination_route_station = None
        route_stations_of_route: list[RouteStation] = list(route.route_stations_of_route.all())
        bookings_of_route_schedule: list[Booking] = list(route_schedule.bookings_of_route_schedule.all())
        
        for route_station in route_stations_of_route:
            if route_station.station.code == input.source_station_code:
                source_route_station = route_station
            elif route_station.station.code == input.destination_station_code:
                destination_route_station = route_station
        
        if not source_route_station or not destination_route_station:
            raise ValueError('Source or destination station not found')
        
        if source_route_station.order >= destination_route_station.order:
            raise ValueError('Source station must come before destination station in route')
        
        seat_availability_data = RouteScheduleModelUtils.get_seat_availability_data(
            schedule=route_schedule,
            journey_date=input.journey_date,
            bookings=bookings_of_route_schedule,
            source_route_station=source_route_station,
            destination_route_station=destination_route_station,
            route_stations_of_route=route_stations_of_route,
        )
        booking_windows_data = RouteScheduleModelUtils.get_booking_windows_data(
            schedule=route_schedule,
            journey_date=input.journey_date,
            source_route_station=source_route_station,
        )

        return TrainAvailabilityStatusService.Output(
            booking_windows_data=booking_windows_data,
            seat_availability_data=seat_availability_data,
            destination_route_station=destination_route_station,
            source_route_station=source_route_station,
        )