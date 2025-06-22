from django.utils import timezone
from bookings.models import Booking
from datetime import datetime, timedelta, date
from utils.enums import BookingStatus, BookingType
from trains.models import RouteSchedule, Route, RouteStation, Train, Station
from trains.dataclasses import RouteScheduleBookingWindowsData, RouteScheduleSeatAvailabilityData


class StationModelUtils:
    pass


class TrainModelUtils:
    pass


class RouteModelUtils:
    
    @staticmethod
    def get_total_duration_minutes(
        source_route_station: RouteStation | None = None,
        destination_route_station: RouteStation | None = None,
        route_stations_of_route: list[RouteStation] | None = None,
        route: Route | None = None,
    ) -> int:
        if source_route_station and destination_route_station:
            ordered_route_stations = sorted([source_route_station, destination_route_station], key=lambda x: x.order)
        elif route_stations_of_route:
            ordered_route_stations = sorted(list(route_stations_of_route), key=lambda x: x.order)
        elif route:
            ordered_route_stations = sorted(list(route.route_stations_of_route.all()), key=lambda x: x.order)
        else:
            raise ValueError('Either source_route_station, destination_route_station or route must be provided')
        
        return int(ordered_route_stations[-1].arrival_minutes_from_source - ordered_route_stations[0].departure_minutes_from_source)
    
    @staticmethod
    def get_total_distance_kms(
        source_route_station: RouteStation | None = None,
        destination_route_station: RouteStation | None = None,
        route_stations_of_route: list[RouteStation] | None = None,
        route: Route | None = None,
    ) -> float:
        if source_route_station and destination_route_station:
            ordered_route_stations = sorted([source_route_station, destination_route_station], key=lambda x: x.order)
        elif route_stations_of_route:
            ordered_route_stations = sorted(list(route_stations_of_route), key=lambda x: x.order)
        elif route:
            ordered_route_stations = sorted(list(route.route_stations_of_route.all()), key=lambda x: x.order)
        else:
            raise ValueError('Either source_route_station, destination_route_station or route must be provided')
        
        return float(ordered_route_stations[-1].distance_kms_from_source - ordered_route_stations[0].distance_kms_from_source)


class RouteStationModelUtils:
    pass


class RouteScheduleModelUtils:

    @staticmethod
    def get_booking_windows_data(
        journey_date: date, 
        schedule: RouteSchedule, 
        source_route_station: RouteStation,
    ) -> RouteScheduleBookingWindowsData:
        now = timezone.now()
        departure_datetime = timezone.make_aware(datetime.combine(journey_date, schedule.departure_time))
        departure_datetime = departure_datetime + timedelta(minutes=source_route_station.departure_minutes_from_source)
        
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
        journey_date: date,
        schedule: RouteSchedule,
        bookings: list[Booking],
        source_route_station: RouteStation,
        destination_route_station: RouteStation,
        route_stations_of_route: list[RouteStation],
    ) -> RouteScheduleSeatAvailabilityData:
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

        route = schedule.route
        general_pricing = (journey_distance_kms / route_total_distance_kms) * route.general_price
        tatkal_pricing = (journey_distance_kms / route_total_distance_kms) * route.tatkal_price

        total_seats = schedule.route.total_seats
        tatkal_seats = schedule.route.tatkal_seats
        general_seats = total_seats - tatkal_seats
        journey_pricing = dict(
            general=general_pricing,
            tatkal=tatkal_pricing,
        )
        
        booking_windows_data = RouteScheduleModelUtils.get_booking_windows_data(
            schedule=schedule,
            journey_date=journey_date,
            source_route_station=source_route_station,
        )

        overlapping_bookings: list[Booking] = []
        for booking in bookings:
            booking_from_order = booking.from_route_station.order
            booking_to_order = booking.to_route_station.order
            if max(source_route_station.order, booking_from_order) < min(destination_route_station.order, booking_to_order):
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

        if booking_windows_data.tatkal_booking_open:
            available_tatkal_seats = (tatkal_seats - confirmed_tatkal_seats)
            available_tatkal_seats += (general_seats - confirmed_general_seats)
            available_general_seats = 0
        elif booking_windows_data.general_booking_open:
            available_tatkal_seats = 0
            available_general_seats = (general_seats - confirmed_general_seats)
        else:
            available_tatkal_seats = 0
            available_general_seats = 0
        
        return RouteScheduleSeatAvailabilityData(
            route_schedule=schedule,
            total_seats=total_seats,
            tatkal_seats=tatkal_seats,
            general_seats=general_seats,
            available_tatkal_seats=available_tatkal_seats,
            available_general_seats=available_general_seats,
            confirmed_general_seats=confirmed_general_seats,
            confirmed_tatkal_seats=confirmed_tatkal_seats,
            waiting_general_seats=waiting_general_seats,
            cancelled_general_seats=cancelled_general_seats,
            route_total_distance_kms=route_total_distance_kms,
            journey_duration_minutes=journey_duration_minutes,
            journey_distance_kms=journey_distance_kms,
            journey_pricing=journey_pricing,
            pricing=route.pricing,
        )
