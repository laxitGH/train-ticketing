from dataclasses import dataclass
from django.utils import timezone
from dataclasses_json import dataclass_json
from datetime import datetime, date, timedelta
from utils.enums import BookingType, BookingStatus
from trains.model_utils import RouteModelUtils
from trains.models import Schedule, Stop
from rest_framework import serializers
from bookings.models import Booking


class JourneyDetailsService:

    @dataclass_json
    @dataclass
    class Input:
        schedule: Schedule
        journey_date: date
        destination_stop: Stop
        source_stop: Stop

    @dataclass_json
    @dataclass
    class SeatAvailability:
        general: int
        tatkal: int

    @dataclass_json
    @dataclass
    class SeatDetails:
        total: int
        seats: 'JourneyDetailsService.SeatAvailability'
        available_seats: 'JourneyDetailsService.SeatAvailability'
        confirmed_seats: 'JourneyDetailsService.SeatAvailability'
        cancelled_seats: 'JourneyDetailsService.SeatAvailability'
        waiting_seats: 'JourneyDetailsService.SeatAvailability'

    @dataclass_json
    @dataclass
    class BookingWindowDetails:
        departure_datetime: datetime
        tatkal_booking_opening_datetime: datetime
        tatkal_booking_closing_datetime: datetime
        general_booking_opening_datetime: datetime
        general_booking_closing_datetime: datetime
        general_booking_open: bool
        tatkal_booking_open: bool

    @dataclass_json
    @dataclass
    class Pricing:
        general: float
        tatkal: float

    @dataclass_json
    @dataclass
    class GeneralDetails:
        pricing: 'JourneyDetailsService.Pricing'
        duration_minutes: int
        distance_kms: float

    @dataclass_json
    @dataclass
    class CompleteDetails:
        seat_details: 'JourneyDetailsService.SeatDetails'
        general_details: 'JourneyDetailsService.GeneralDetails'
        booking_window_details: 'JourneyDetailsService.BookingWindowDetails'

    class SeatDetailsSerializer(serializers.Serializer):
        def to_representation(self, instance: 'JourneyDetailsService.SeatDetails'):
            return instance.to_dict()

    class GeneralDetailsSerializer(serializers.Serializer):
        def to_representation(self, instance: 'JourneyDetailsService.GeneralDetails'):
            return instance.to_dict()

    class BookingWindowDetailsSerializer(serializers.Serializer):
        def to_representation(self, instance: 'JourneyDetailsService.BookingWindowDetails'):
            return instance.to_dict()

    class CompleteDetailsSerializer(serializers.Serializer):
        seat_details = serializers.SerializerMethodField()
        general_details = serializers.SerializerMethodField()
        booking_window_details = serializers.SerializerMethodField()
        
        def get_seat_details(self, obj):
            return obj.seat_details.to_dict()
        
        def get_general_details(self, obj):
            return obj.general_details.to_dict()
        
        def get_booking_window_details(self, obj):
            return obj.booking_window_details.to_dict()

    def __init__(self, input: 'JourneyDetailsService.Input'):
        self.schedule = input.schedule
        self.journey_date = input.journey_date
        self.destination_stop = input.destination_stop
        self.source_stop = input.source_stop

        self.seat_details: JourneyDetailsService.SeatDetails | None = None
        self.journey_details: JourneyDetailsService.GeneralDetails | None = None
        self.booking_window_details: JourneyDetailsService.BookingWindowDetails | None = None

    def get_complete_details(self, journey_bookings: list[Booking]) -> 'JourneyDetailsService.CompleteDetails':
        self.booking_window_details = self.get_booking_window_details()
        self.seat_details = self.get_seat_details(journey_bookings)
        self.journey_details = self.get_journey_details()

        return JourneyDetailsService.CompleteDetails(
            booking_window_details=self.booking_window_details,
            general_details=self.journey_details,
            seat_details=self.seat_details,
        )

    def get_seat_details(self, journey_bookings: list[Booking]) -> 'JourneyDetailsService.SeatDetails':
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

        seats = JourneyDetailsService.SeatAvailability(
            general=general_seats,
            tatkal=tatkal_seats,
        )
        available_seats = JourneyDetailsService.SeatAvailability(
            general=available_general_seats,
            tatkal=available_tatkal_seats,
        )
        confirmed_seats = JourneyDetailsService.SeatAvailability(
            general=confirmed_general_seats,
            tatkal=confirmed_tatkal_seats,
        )
        cancelled_seats = JourneyDetailsService.SeatAvailability(
            general=cancelled_general_seats,
            tatkal=0,
        )
        waiting_seats = JourneyDetailsService.SeatAvailability(
            general=waiting_general_seats,
            tatkal=0,
        )

        self.seat_details = JourneyDetailsService.SeatDetails(
            seats=seats,
            total=total_seats,
            available_seats=available_seats,
            confirmed_seats=confirmed_seats,
            cancelled_seats=cancelled_seats,
            waiting_seats=waiting_seats,
        )

        return self.seat_details

    def get_booking_window_details(self) -> 'JourneyDetailsService.BookingWindowDetails':
        if self.booking_window_details:
            return self.booking_window_details

        now = timezone.now()
        departure_datetime = timezone.make_aware(datetime.combine(
            self.journey_date, self.schedule.departure_time))
        departure_datetime = departure_datetime + \
            timedelta(minutes=self.source_stop.departure_minutes_from_source)
        general_booking_opening_datetime = departure_datetime - \
            timedelta(days=120)
        general_booking_closing_datetime = departure_datetime - \
            timedelta(hours=4)

        tatkal_booking_opening_datetime = departure_datetime - \
            timedelta(hours=2)
        tatkal_booking_closing_datetime = departure_datetime - \
            timedelta(hours=2, minutes=-10)

        self.booking_window_details = JourneyDetailsService.BookingWindowDetails(
            departure_datetime=departure_datetime,
            tatkal_booking_opening_datetime=tatkal_booking_opening_datetime,
            tatkal_booking_closing_datetime=tatkal_booking_closing_datetime,
            general_booking_opening_datetime=general_booking_opening_datetime,
            general_booking_closing_datetime=general_booking_closing_datetime,
            general_booking_open=general_booking_opening_datetime <= now <= general_booking_closing_datetime,
            tatkal_booking_open=tatkal_booking_opening_datetime <= now <= tatkal_booking_closing_datetime,
        )

        return self.booking_window_details

    def get_journey_details(self) -> 'JourneyDetailsService.GeneralDetails':
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

        stops_of_route: list[Stop] = list(
            self.schedule.route.stops_of_route.all())
        route_total_distance_kms = RouteModelUtils.get_total_distance_kms(
            stops_of_route=stops_of_route,
        )

        general_pricing = (
            journey_distance_kms / route_total_distance_kms) * self.schedule.route.general_price
        tatkal_pricing = (
            journey_distance_kms / route_total_distance_kms) * self.schedule.route.tatkal_price

        self.journey_details = JourneyDetailsService.GeneralDetails(
            distance_kms=journey_distance_kms,
            duration_minutes=journey_duration_minutes,
            pricing=JourneyDetailsService.Pricing(
                general=round(general_pricing, 2),
                tatkal=round(tatkal_pricing, 2),
            ),
        )

        return self.journey_details
