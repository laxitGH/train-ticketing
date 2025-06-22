from datetime import datetime
from dataclasses import dataclass
from dataclasses_json import dataclass_json


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
    available_tatkal_seats: int
    available_general_seats: int
    confirmed_general_seats: int
    confirmed_tatkal_seats: int
    waiting_general_seats: int
    cancelled_general_seats: int
