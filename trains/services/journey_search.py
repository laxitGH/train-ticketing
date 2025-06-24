from typing import Optional
from datetime import date
from trains.models import Stop
from dataclasses import dataclass
from bookings.models import Booking
from dataclasses_json import dataclass_json
from django.contrib.auth.models import User
from trains.selectors import ScheduleSelectors, BookingSelectors, StopSelectors
from trains.serializers import RouteSerializers, StopSerializers, ScheduleSerializers
from trains.services.journey_details import JourneyDetailsService
from trains.models import Schedule, Route, Station, Train


class JourneySearchService:

    @dataclass_json
    @dataclass
    class Input:
        journey_date: date
        source_station_code: str
        destination_station_code: str
        schedule_query_options: 'Optional[ScheduleSelectors.Options]' = None
        booking_query_options: 'Optional[BookingSelectors.Options]' = None
        stop_query_options: 'Optional[StopSelectors.Options]' = None
        
    class StopOutputModel(Stop):
        station: Station  
        class Meta:
            abstract = True
        
    class RouteOutputModel(Route):
        train: Train
        stops_of_route: list['JourneySearchService.StopOutputModel']
        class Meta:
            abstract = True
        
    class BookingOutputModel(Booking):
        user: User
        to_stop: Stop
        from_stop: Stop
        class Meta:
            abstract = True

    class ScheduleOutputModel(Schedule):
        route: 'JourneySearchService.RouteOutputModel'
        stops: list['JourneySearchService.StopOutputModel']
        source_stop: 'JourneySearchService.StopOutputModel'
        destination_stop: 'JourneySearchService.StopOutputModel'
        bookings_of_schedule: list['JourneySearchService.BookingOutputModel']
        booking_window_details: JourneyDetailsService.BookingWindowDetails
        general_details: JourneyDetailsService.GeneralDetails
        class Meta:
            managed = False

    class OutputSerializer(ScheduleSerializers.ModelSerializer):
        route = RouteSerializers.ModelSerializerWithTrain()
        source_stop = StopSerializers.ModelSerializerWithStation()
        stops = StopSerializers.ModelSerializerWithStation(many=True)
        destination_stop = StopSerializers.ModelSerializerWithStation()
        booking_window_details = JourneyDetailsService.BookingWindowDetailsSerializer()
        general_details = JourneyDetailsService.GeneralDetailsSerializer()
        seat_details = JourneyDetailsService.SeatDetailsSerializer()

    def __init__(self, input: 'JourneySearchService.Input'):
        self.journey_date = input.journey_date
        self.source_station_code = input.source_station_code
        self.destination_station_code = input.destination_station_code
        self.schedule_query_options = input.schedule_query_options
        self.booking_query_options = input.booking_query_options
        self.stop_query_options = input.stop_query_options

    def search_journeys(self, journey_date: date | None = None) -> list[ScheduleOutputModel]:
        new_journey_date = journey_date or self.journey_date
        schedules_queryset = ScheduleSelectors.get_schedule_complete_details_queryset(
            query_options=self.schedule_query_options,
            booking_query_options=self.booking_query_options,
            stop_query_options=self.stop_query_options,
            journey_date=new_journey_date,
        )

        valid_schedules: list[JourneySearchService.Output] = []
        for schedule in schedules_queryset:
            route = schedule.route
            stops_of_route: list[Stop] = list(route.stops_of_route.all())
            bookings_of_schedule: list[Booking] = list(schedule.bookings_of_schedule.all())

            destination_stop: Stop = None
            source_stop: Stop = None

            for stop in stops_of_route:
                if stop.station.code == self.source_station_code:
                    source_stop = stop
                elif stop.station.code == self.destination_station_code:
                    destination_stop = stop

            if (
                source_stop and
                destination_stop and
                source_stop.order < destination_stop.order
            ):
                setattr(schedule, 'source_stop', source_stop)
                setattr(schedule, 'destination_stop', destination_stop)
                valid_schedules.append(schedule)

        for schedule in valid_schedules:
            route = schedule.route
            stops_of_route: list[Stop] = list(route.stops_of_route.all())
            bookings_of_schedule: list[Booking] = list(schedule.bookings_of_schedule.all())

            source_stop: Stop = getattr(schedule, 'source_stop')
            destination_stop: Stop = getattr(schedule, 'destination_stop')

            journey_details_service = JourneyDetailsService(
                input=JourneyDetailsService.Input(
                    schedule=schedule,
                    journey_date=new_journey_date,
                    destination_stop=destination_stop,
                    source_stop=source_stop,
                )
            )

            complete_details = journey_details_service.get_complete_details(journey_bookings=bookings_of_schedule)
            setattr(schedule, 'booking_window_details', complete_details.booking_window_details)
            setattr(schedule, 'general_details', complete_details.general_details)
            setattr(schedule, 'seat_details', complete_details.seat_details)
            setattr(schedule, 'stops', stops_of_route)

        return valid_schedules
