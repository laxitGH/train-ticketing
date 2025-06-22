from rest_framework import serializers
from trains.models import Train, Route, RouteStation, RouteSchedule, Station


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = '__all__'


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = '__all__'


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'


class RouteStationSerializer(serializers.ModelSerializer):    
    class Meta:
        model = RouteStation
        fields = '__all__'

class RouteStationWithStationSerializer(RouteStationSerializer):
    station = StationSerializer()


class RouteScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteSchedule
        fields = '__all__'
