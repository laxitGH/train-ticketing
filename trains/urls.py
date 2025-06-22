from django.urls import path
from trains.views import journey_search_view, journey_details_view

urlpatterns = [
    path('search/', journey_search_view, name='journey-search'),
    path('details/', journey_details_view, name='journey-details'),
]
