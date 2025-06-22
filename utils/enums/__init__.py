from enum import Enum


class BookingType(Enum):
    GENERAL = 'general'
    TATKAL = 'tatkal'


class BookingStatus(Enum):
    WAITING = 'waiting'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
