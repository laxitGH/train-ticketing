from django.urls import path
from bookings.views import booking_create_view, booking_cancel_view, booking_details_view, user_bookings_list_view

urlpatterns = [
	path('create/', booking_create_view, name='booking-create'),
	path('cancel/', booking_cancel_view, name='booking-cancel'),
	path('details/', booking_details_view, name='booking-details'),
	path('user-bookings/', user_bookings_list_view, name='user-bookings-list'),
]