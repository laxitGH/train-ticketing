from bookings.models import Booking
from utils.selectors import BaseSelectors


class BookingSelectors(BaseSelectors):
    model = Booking