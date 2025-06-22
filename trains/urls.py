from django.urls import path
from trains.views import train_search_view, train_seat_availability_view

urlpatterns = [
    path('search/', train_search_view, name='train-search'),
    path('seat-availability/', train_seat_availability_view, name='train-seat-availability'),
]
