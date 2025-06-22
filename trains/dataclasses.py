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
    general_booking_open: bool
    tatkal_booking_open: bool
