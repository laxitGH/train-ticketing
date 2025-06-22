from django.utils import timezone
from bookings.models import Booking
from trains.models import RouteSchedule
from datetime import datetime, timedelta, date
from utils.enums import BookingStatus, BookingType
from trains.dataclasses import RouteScheduleBookingWindowsData, RouteScheduleSeatAvailabilityData


class RouteScheduleModelUtils:

    @staticmethod
    def get_booking_windows_data(schedule: RouteSchedule, journey_date: date) -> RouteScheduleBookingWindowsData:
        now = timezone.now()
        departure_datetime = timezone.make_aware(datetime.combine(journey_date, schedule.departure_time))
        
        general_booking_opening_datetime = departure_datetime - timedelta(days=120)
        general_booking_closing_datetime = departure_datetime - timedelta(hours=4)
        
        tatkal_booking_opening_datetime = departure_datetime - timedelta(hours=2)
        tatkal_booking_closing_datetime = departure_datetime - timedelta(hours=2, minutes=-10)
        
        return RouteScheduleBookingWindowsData(
            departure_datetime=departure_datetime,
            tatkal_booking_opening_datetime=tatkal_booking_opening_datetime,
            tatkal_booking_closing_datetime=tatkal_booking_closing_datetime,
            general_booking_opening_datetime=general_booking_opening_datetime,
            general_booking_closing_datetime=general_booking_closing_datetime,
            general_booking_open=general_booking_opening_datetime <= now <= general_booking_closing_datetime,
            tatkal_booking_open=tatkal_booking_opening_datetime <= now <= tatkal_booking_closing_datetime,
        )
    
    @staticmethod
    def get_seat_availability_data(
        schedule: RouteSchedule,
        bookings: list[Booking],
        journey_date: date,
    ) -> RouteScheduleSeatAvailabilityData:
        total_seats = schedule.route.total_seats
        tatkal_seats = schedule.route.tatkal_seats
        general_seats = total_seats - tatkal_seats
        
        now = timezone.now()
        booking_windows_data = RouteScheduleModelUtils.get_booking_windows_data(
            journey_date=journey_date,
            schedule=schedule,
        )

        confirmed_general_seats = len([
            booking for booking in bookings 
            if (booking.type == BookingType.GENERAL.value and booking.status == BookingStatus.CONFIRMED.value)
        ])
        confirmed_tatkal_seats = len([
            booking for booking in bookings 
            if (booking.type == BookingType.TATKAL.value and booking.status == BookingStatus.CONFIRMED.value)
        ])
        waiting_general_seats = len([
            booking for booking in bookings 
            if (booking.type == BookingType.GENERAL.value and booking.status == BookingStatus.WAITING.value)
        ])
        cancelled_general_seats = len([
            booking for booking in bookings 
            if (booking.type == BookingType.GENERAL.value and booking.status == BookingStatus.CANCELLED.value)
        ])
        cancelled_tatkal_seats = len([
            booking for booking in bookings 
            if (booking.type == BookingType.TATKAL.value and booking.status == BookingStatus.CANCELLED.value)
        ])

        if booking_windows_data.tatkal_booking_open:
            available_tatkal_seats = (tatkal_seats - confirmed_tatkal_seats)
            available_tatkal_seats += (general_seats - confirmed_general_seats if general_seats - confirmed_general_seats > 0 else 0)
            available_general_seats = 0
        elif booking_windows_data.general_booking_open:
            available_tatkal_seats = 0
            available_general_seats = (general_seats - confirmed_general_seats)
        else:
            available_tatkal_seats = 0
            available_general_seats = 0
        
        return RouteScheduleSeatAvailabilityData(
            total_seats=total_seats,
            tatkal_seats=tatkal_seats,
            general_seats=general_seats,
            available_tatkal_seats=available_tatkal_seats,
            available_general_seats=available_general_seats,
            confirmed_general_seats=confirmed_general_seats,
            confirmed_tatkal_seats=confirmed_tatkal_seats,
            waiting_general_seats=waiting_general_seats,
            cancelled_general_seats=cancelled_general_seats,
            cancelled_tatkal_seats=cancelled_tatkal_seats,
        )


class RouteUtils:
    pass


class RouteStationUtils:
    pass


class StationUtils:
    pass


class TrainUtils:
    pass