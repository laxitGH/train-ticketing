from datetime import date
from django.utils import timezone
from django.db.models import QuerySet
from django.db.models.query import Prefetch
from trains.models import RouteSchedule, RouteStation, Route, Train, Station
from bookings.models import Booking


class StationSelectors:
    pass


class TrainSelectors:
    pass


class RouteSelectors:
    pass


class RouteStationSelectors:
    pass


class RouteScheduleSelectors:

    @staticmethod
    def get_schedule_details_queryset(
        main_filters: dict,
        journey_date: date,
        route_station_filters: dict = {},
        booking_filters: dict = {},
    ) -> QuerySet[RouteSchedule]:
        new_main_filters = { **main_filters }
        new_booking_filters = { **booking_filters }
        new_route_station_filters = { **route_station_filters }
        
        now = timezone.now().date()
        if journey_date < now:
            raise ValueError('Journey date cannot be in the past')
        
        new_main_filters['weekday'] = journey_date.strftime('%a').upper()[:3]
        new_booking_filters['journey_date'] = journey_date

        return (
            RouteSchedule.objects.filter(**new_main_filters)
            .select_related('route__train').prefetch_related(
                Prefetch(   
                    'route__route_stations_of_route',
                    queryset=RouteStation.objects.filter(
                        **new_route_station_filters
                    ).select_related('station').order_by('order'),
                    to_attr='stations_of_schedule'
                ),
                Prefetch(
                    'bookings_of_route_schedule',
                    queryset=Booking.objects.filter(
                        **new_booking_filters
                    ).select_related('user'),
                    to_attr='bookings_of_schedule'
                )
            ).distinct()
        )
