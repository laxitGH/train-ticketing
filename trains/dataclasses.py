from datetime import datetime
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from trains.models import RouteSchedule


@dataclass_json
@dataclass
class RouteScheduleBookingWindowsData:
    tatkal_booking_opening_datetime: datetime
    tatkal_booking_closing_datetime: datetime
    general_booking_opening_datetime: datetime
    general_booking_closing_datetime: datetime
    departure_datetime: datetime
    general_booking_open: bool
    tatkal_booking_open: bool


@dataclass_json
@dataclass
class RouteScheduleSeatAvailabilityData:
    total_seats: int
    tatkal_seats: int
    general_seats: int
    route_schedule: RouteSchedule
    available_tatkal_seats: int
    available_general_seats: int
    confirmed_general_seats: int
    confirmed_tatkal_seats: int
    waiting_general_seats: int
    journey_distance_kms: float
    cancelled_general_seats: int
    route_total_distance_kms: float
    journey_duration_minutes: int
    journey_pricing: dict[str, float]
    pricing: dict[str, float]
