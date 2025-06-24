from enum import Enum


class BookingType(Enum):
    GENERAL = 'general'
    TATKAL = 'tatkal'

    @classmethod
    def choices(cls):
        return [(item.value, item.value) for item in cls]


class BookingStatus(Enum):
    WAITING = 'waiting'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'

    @classmethod
    def choices(cls):
        return [(item.value, item.value) for item in cls]
