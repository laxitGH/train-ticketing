from dataclasses import dataclass
from datetime import datetime, date
from dataclasses_json import dataclass_json
from trains.models import Schedule, Stop, Route


class JourneyDetailsServiceDataclasses:

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
        seats: 'JourneyDetailsServiceDataclasses.SeatAvailability'
        available_seats: 'JourneyDetailsServiceDataclasses.SeatAvailability'
        confirmed_seats: 'JourneyDetailsServiceDataclasses.SeatAvailability'
        cancelled_seats: 'JourneyDetailsServiceDataclasses.SeatAvailability'
        waiting_seats: 'JourneyDetailsServiceDataclasses.SeatAvailability'

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
        pricing: 'JourneyDetailsServiceDataclasses.Pricing'
        duration_minutes: int
        distance_kms: float

    @dataclass_json
    @dataclass
    class CompleteDetails:
        seat_details: 'JourneyDetailsServiceDataclasses.SeatDetails'
        general_details: 'JourneyDetailsServiceDataclasses.GeneralDetails'
        booking_window_details: 'JourneyDetailsServiceDataclasses.BookingWindowDetails'
    

class JourneySearchServiceDataclasses:

    @dataclass_json
    @dataclass
    class Input:
        journey_date: date
        source_station_code: str
        destination_station_code: str

    class Output(Schedule):
        route: Route
        stops: list[Stop]
        source_stop: Stop
        destination_stop: Stop
        booking_window_details: dict
        general_details: dict
        seat_details: dict