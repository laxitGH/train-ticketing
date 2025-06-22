from trains.models import Stop
from django.utils import timezone
from bookings.models import Booking
from datetime import date, datetime, timedelta
from trains.selectors import ScheduleSelectors
from trains.model_utils import RouteModelUtils
from utils.enums import BookingStatus, BookingType
from trains.dataclasses import JourneyDetailsServiceDataclasses, JourneySearchServiceDataclasses


class JourneyDetailsService:
    def __init__(self, input: JourneyDetailsServiceDataclasses.Input):
        self.schedule = input.schedule
        self.journey_date = input.journey_date
        self.destination_stop = input.destination_stop
        self.source_stop = input.source_stop

        self.seat_details: JourneyDetailsServiceDataclasses.SeatDetails | None = None
        self.journey_details: JourneyDetailsServiceDataclasses.GeneralDetails | None = None
        self.booking_window_details: JourneyDetailsServiceDataclasses.BookingWindowDetails | None = None

    def get_complete_details(self, journey_bookings: list[Booking]) -> JourneyDetailsServiceDataclasses.CompleteDetails:
        self.booking_window_details = self.get_booking_window_details()
        self.seat_details = self.get_seat_details(journey_bookings)
        self.journey_details = self.get_journey_details()

        return JourneyDetailsServiceDataclasses.CompleteDetails(
            booking_window_details=self.booking_window_details,
            general_details=self.journey_details,
            seat_details=self.seat_details,
        )

    def get_seat_details(self, journey_bookings: list[Booking]) -> JourneyDetailsServiceDataclasses.SeatDetails:
        if self.seat_details:
            return self.seat_details
        
        self.get_booking_window_details()
        total_seats = self.schedule.route.total_seats
        tatkal_seats = self.schedule.route.tatkal_seats
        general_seats = self.schedule.route.general_seats

        overlapping_bookings: list[Booking] = []
        for booking in journey_bookings:
            booking_to_order = booking.to_stop.order
            booking_from_order = booking.from_stop.order
            if max(self.source_stop.order, booking_from_order) < min(self.destination_stop.order, booking_to_order):
                overlapping_bookings.append(booking)

        waiting_general_seats = 0
        confirmed_tatkal_seats = 0
        confirmed_general_seats = 0
        cancelled_general_seats = 0
        
        for booking in overlapping_bookings:
            if booking.type == BookingType.GENERAL.value:
                if booking.status == BookingStatus.CONFIRMED.value:
                    confirmed_general_seats += 1
                elif booking.status == BookingStatus.WAITING.value:
                    waiting_general_seats += 1
                elif booking.status == BookingStatus.CANCELLED.value:
                    cancelled_general_seats += 1
            elif booking.type == BookingType.TATKAL.value:
                if booking.status == BookingStatus.CONFIRMED.value:
                    confirmed_tatkal_seats += 1

        if self.booking_window_details.tatkal_booking_open:
            available_tatkal_seats = (tatkal_seats - confirmed_tatkal_seats)
            available_tatkal_seats += (general_seats - confirmed_general_seats)
            available_general_seats = 0
        elif self.booking_window_details.general_booking_open:
            available_tatkal_seats = 0
            available_general_seats = (general_seats - confirmed_general_seats)
        else:
            available_tatkal_seats = 0
            available_general_seats = 0

        seats = JourneyDetailsServiceDataclasses.SeatAvailability(
            general=general_seats,
            tatkal=tatkal_seats,
        )
        available_seats = JourneyDetailsServiceDataclasses.SeatAvailability(
            general=available_general_seats,
            tatkal=available_tatkal_seats,
        )
        confirmed_seats = JourneyDetailsServiceDataclasses.SeatAvailability(
            general=confirmed_general_seats,
            tatkal=confirmed_tatkal_seats,
        )
        cancelled_seats = JourneyDetailsServiceDataclasses.SeatAvailability(
            general=cancelled_general_seats,
            tatkal=0,
        )
        waiting_seats = JourneyDetailsServiceDataclasses.SeatAvailability(
            general=waiting_general_seats,
            tatkal=0,
        )
        
        self.seat_details = JourneyDetailsServiceDataclasses.SeatDetails(
            seats=seats,
            total=total_seats,
            available_seats=available_seats,
            confirmed_seats=confirmed_seats,
            cancelled_seats=cancelled_seats,
            waiting_seats=waiting_seats,
        )

        return self.seat_details

    def get_booking_window_details(self) -> JourneyDetailsServiceDataclasses.BookingWindowDetails:
        if self.booking_window_details:
            return self.booking_window_details
        
        now = timezone.now()
        departure_datetime = timezone.make_aware(datetime.combine(self.journey_date, self.schedule.departure_time))
        departure_datetime = departure_datetime + timedelta(minutes=self.source_stop.departure_minutes_from_source)
        general_booking_opening_datetime = departure_datetime - timedelta(days=120)
        general_booking_closing_datetime = departure_datetime - timedelta(hours=4)
        
        tatkal_booking_opening_datetime = departure_datetime - timedelta(hours=2)
        tatkal_booking_closing_datetime = departure_datetime - timedelta(hours=2, minutes=-10)
        
        self.booking_window_details = JourneyDetailsServiceDataclasses.BookingWindowDetails(
            departure_datetime=departure_datetime,
            tatkal_booking_opening_datetime=tatkal_booking_opening_datetime,
            tatkal_booking_closing_datetime=tatkal_booking_closing_datetime,
            general_booking_opening_datetime=general_booking_opening_datetime,
            general_booking_closing_datetime=general_booking_closing_datetime,
            general_booking_open=general_booking_opening_datetime <= now <= general_booking_closing_datetime,
            tatkal_booking_open=tatkal_booking_opening_datetime <= now <= tatkal_booking_closing_datetime,
        )

        return self.booking_window_details

    def get_journey_details(self) -> JourneyDetailsServiceDataclasses.GeneralDetails:
        if self.journey_details:
            return self.journey_details
        
        journey_duration_minutes = RouteModelUtils.get_total_duration_minutes(
            source_stop=self.source_stop,
            destination_stop=self.destination_stop,
        )
        journey_distance_kms = RouteModelUtils.get_total_distance_kms(
            source_stop=self.source_stop,
            destination_stop=self.destination_stop,
        )

        stops_of_route: list[Stop] = list(self.schedule.route.stops_of_route.all())
        route_total_distance_kms = RouteModelUtils.get_total_distance_kms(
            stops_of_route=stops_of_route,
        )

        general_pricing = (journey_distance_kms / route_total_distance_kms) * self.schedule.route.general_price
        tatkal_pricing = (journey_distance_kms / route_total_distance_kms) * self.schedule.route.tatkal_price

        self.journey_details = JourneyDetailsServiceDataclasses.GeneralDetails(
            distance_kms=journey_distance_kms,
            duration_minutes=journey_duration_minutes,
            pricing=JourneyDetailsServiceDataclasses.Pricing(
                general=round(general_pricing, 2),
                tatkal=round(tatkal_pricing, 2),
            ),
        )

        return self.journey_details


class JourneySearchService:
    def __init__(self, input: JourneySearchServiceDataclasses.Input):
        self.journey_date = input.journey_date
        self.source_station_code = input.source_station_code
        self.destination_station_code = input.destination_station_code

    def search_journeys(
        self, 
        main_filters: dict = {},
        stop_filters: dict = {},
        booking_filters: dict = {},
        journey_date: date | None = None,
    ) -> list[JourneySearchServiceDataclasses.Output]:
        journey_date = journey_date or self.journey_date
        
        new_main_filters = { **main_filters }
        new_stop_filters = { **stop_filters }
        new_booking_filters = { **booking_filters }

        schedules_queryset = ScheduleSelectors.get_schedule_complete_details_queryset(
            booking_filters=new_booking_filters,
            stop_filters=new_stop_filters,
            main_filters=new_main_filters,
            journey_date=journey_date,
        )

        valid_schedules: list[JourneySearchServiceDataclasses.Output] = []
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
                setattr(schedule, 'destination_stop',destination_stop)
                valid_schedules.append(schedule)

        for schedule in valid_schedules:
            route = schedule.route
            stops_of_route: list[Stop] = list(route.stops_of_route.all())
            bookings_of_schedule: list[Booking] = list(schedule.bookings_of_schedule.all())

            source_stop: Stop = getattr(schedule, 'source_stop')
            destination_stop: Stop = getattr(schedule, 'destination_stop')

            journey_details_service = JourneyDetailsService(
                input=JourneyDetailsServiceDataclasses.Input(
                    schedule=schedule,
                    journey_date=journey_date,
                    destination_stop=destination_stop,
                    source_stop=source_stop,
                )
            )

            complete_details = journey_details_service.get_complete_details(journey_bookings=bookings_of_schedule)
            setattr(schedule, 'booking_window_details', complete_details.booking_window_details.to_dict())
            setattr(schedule, 'general_details', complete_details.general_details.to_dict())
            setattr(schedule, 'seat_details', complete_details.seat_details.to_dict())
            setattr(schedule, 'stops', stops_of_route)

        return valid_schedules
