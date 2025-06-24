from datetime import date
from django.utils import timezone
from django.db.models import QuerySet
from django.db.models.query import Prefetch
from trains.models import Schedule, Stop, Train, Route, Station
from bookings.selectors import BookingSelectors
from utils.selectors import BaseSelectors


class StationSelectors(BaseSelectors):
    model = Station


class TrainSelectors(BaseSelectors):
    model = Train
    
    @staticmethod
    def get_train_complete_details_queryset(
        query_options: 'TrainSelectors.Options | None' = None,
        stop_query_options: 'StopSelectors.Options | None' = None,
        route_query_options: 'RouteSelectors.Options | None' = None,
        schedule_query_options: 'ScheduleSelectors.Options | None' = None,
    ) -> QuerySet[Train]:
        trains_queryset = TrainSelectors.generate_queryset(query_options)
        stops_queryset = StopSelectors.generate_queryset(stop_query_options)
        routes_queryset = RouteSelectors.generate_queryset(route_query_options)
        schedules_queryset = ScheduleSelectors.generate_queryset(schedule_query_options)

        return (
            trains_queryset.prefetch_related(
                Prefetch(
                    'routes_of_train', 
                    queryset=routes_queryset.prefetch_related(
                        Prefetch(
                            'stops_of_route', 
                            queryset=stops_queryset.select_related('station')
                        ),
                        Prefetch(
                            'schedules_of_route',
                            queryset=schedules_queryset,
                        ),
                    ),
                )
            )
        )


class RouteSelectors(BaseSelectors):
    model = Route


class StopSelectors(BaseSelectors):
    model = Stop


class ScheduleSelectors(BaseSelectors):
    model = Schedule

    @staticmethod
    def get_schedule_complete_details_queryset(
        query_options: 'ScheduleSelectors.Options | None' = None,
        stop_query_options: 'StopSelectors.Options | None' = None,
        booking_query_options: 'BookingSelectors.Options | None' = None,
        journey_date: date | None = None,
    ) -> QuerySet[Schedule]:
        stops_queryset = StopSelectors.generate_queryset(stop_query_options)
        schedules_queryset = ScheduleSelectors.generate_queryset(query_options)
        bookings_queryset = BookingSelectors.generate_queryset(booking_query_options)
        
        now = timezone.now().date()
        if journey_date:
            if journey_date < now:
                raise ValueError('Journey date cannot be in the past')

            query_options.add_filter('weekday', journey_date.strftime('%a').upper()[:3])
            query_options.add_filter('journey_date', journey_date)

        return (
            schedules_queryset
            .select_related('route__train').prefetch_related(
                Prefetch(   
                    'route__stops_of_route',
                    queryset=stops_queryset.select_related('station').order_by('order'),
                ),
                Prefetch(
                    'bookings_of_schedule',
                    queryset=bookings_queryset.select_related('user', 'from_stop', 'to_stop'),
                )
            ).distinct()
        )
