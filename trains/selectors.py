from datetime import date
from django.utils import timezone
from django.db.models import QuerySet
from django.db.models.query import Prefetch
from trains.models import Schedule, Stop
from bookings.models import Booking


class StationSelectors:
    pass


class TrainSelectors:
    pass


class RouteSelectors:
    pass


class StopSelectors:
    pass


class ScheduleSelectors:

    @staticmethod
    def get_schedule_complete_details_queryset(
        journey_date: date,
        stop_filters: dict = {},
        main_filters: dict = {},
        booking_filters: dict = {},
    ) -> QuerySet[Schedule]:
        new_main_filters = { **main_filters }
        new_stop_filters = { **stop_filters }
        new_booking_filters = { **booking_filters }
        
        now = timezone.now().date()
        if journey_date < now:
            raise ValueError('Journey date cannot be in the past')
        
        new_main_filters['weekday'] = journey_date.strftime('%a').upper()[:3]
        new_booking_filters['journey_date'] = journey_date

        return (
            Schedule.objects.filter(**new_main_filters)
            .select_related('route__train').prefetch_related(
                Prefetch(   
                    'route__stops_of_route',
                    queryset=Stop.objects.filter(
                        **new_stop_filters
                    ).select_related('station').order_by('order'),
                ),
                Prefetch(
                    'bookings_of_schedule',
                    queryset=Booking.objects.filter(
                        **new_booking_filters
                    ).select_related('user', 'from_stop', 'to_stop'),
                )
            ).distinct()
        )
