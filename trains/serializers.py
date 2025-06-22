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


class RouteWithTrainSerializer(RouteSerializer):
    train = TrainSerializer()


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


class RouteScheduleBookingWindowsSerializer(serializers.Serializer):
    tatkal_booking_open = serializers.BooleanField()
    general_booking_open = serializers.BooleanField()
    general_booking_opening_datetime = serializers.DateTimeField()
    general_booking_closing_datetime = serializers.DateTimeField()
    tatkal_booking_opening_datetime = serializers.DateTimeField()
    tatkal_booking_closing_datetime = serializers.DateTimeField()
    departure_datetime = serializers.DateTimeField()


class RouteScheduleSeatAvailabilitySerializer(serializers.Serializer):
    total_seats = serializers.IntegerField()
    tatkal_seats = serializers.IntegerField()
    general_seats = serializers.IntegerField()
    available_tatkal_seats = serializers.IntegerField()
    available_general_seats = serializers.IntegerField()
    confirmed_general_seats = serializers.IntegerField()
    confirmed_tatkal_seats = serializers.IntegerField()
    waiting_general_seats = serializers.IntegerField()
    cancelled_general_seats = serializers.IntegerField()
    cancelled_tatkal_seats = serializers.IntegerField()


class TrainSearchOutputSerializer(RouteScheduleSerializer):
    route = RouteWithTrainSerializer()
    source_route_station = RouteStationWithStationSerializer()
    destination_route_station = RouteStationWithStationSerializer()
    seat_availability_data = RouteScheduleSeatAvailabilitySerializer()
    booking_windows_data = RouteScheduleBookingWindowsSerializer()
    route_stations = RouteStationWithStationSerializer(many=True)
    journey_duration_minutes = serializers.IntegerField()
    journey_distance_kms = serializers.FloatField()
    journey_pricing = serializers.FloatField()
