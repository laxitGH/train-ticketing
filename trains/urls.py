from django.urls import path
from trains.views import TrainSearchAPIView

urlpatterns = [
    path('search/', TrainSearchAPIView.as_view(), name='train-search'),
]
