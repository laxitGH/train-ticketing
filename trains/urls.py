from django.urls import path
from trains.views import train_search_view, train_availability_status_view

urlpatterns = [
    path('search/', train_search_view, name='train-search'),
    path('availability-status/', train_availability_status_view, name='train-availability-status'),
]
