from rest_framework import serializers
from trains.models import Train, Route, RouteStation, RouteSchedule, Station


class StationSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = Station
            fields = '__all__'


class TrainSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = Train
            fields = '__all__'


class RouteSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = Route
            fields = '__all__'

    class ModelSerializerWithTrain(ModelSerializer):
        train = TrainSerializers.ModelSerializer()


class RouteStationSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = RouteStation
            fields = '__all__'

    class ModelSerializerWithStation(ModelSerializer):
        station = StationSerializers.ModelSerializer()

    class ModelSerializerWithRoute(ModelSerializer):
        route = RouteSerializers.ModelSerializer()

    class ModelSerializerWithRouteAndStation(ModelSerializer):
        station = StationSerializers.ModelSerializer()
        route = RouteSerializers.ModelSerializer()


class RouteScheduleSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = RouteSchedule
            fields = '__all__'

    class ModelSerializerWithRoute(ModelSerializer):
        route = RouteSerializers.ModelSerializer()

    class BookingWindowsSerializer(serializers.Serializer):
        tatkal_booking_open = serializers.BooleanField()
        general_booking_open = serializers.BooleanField()
        general_booking_opening_datetime = serializers.DateTimeField()
        general_booking_closing_datetime = serializers.DateTimeField()
        tatkal_booking_opening_datetime = serializers.DateTimeField()
        tatkal_booking_closing_datetime = serializers.DateTimeField()

    class SeatAvailabilitySerializer(serializers.Serializer):
        total_seats = serializers.IntegerField()
        tatkal_seats = serializers.IntegerField()
        general_seats = serializers.IntegerField()
        available_tatkal_seats = serializers.IntegerField()
        available_general_seats = serializers.IntegerField()
        confirmed_general_seats = serializers.IntegerField()
        confirmed_tatkal_seats = serializers.IntegerField()
        waiting_general_seats = serializers.IntegerField()
        cancelled_general_seats = serializers.IntegerField()
        route_total_distance_kms = serializers.FloatField()
        journey_duration_minutes = serializers.IntegerField()
        journey_distance_kms = serializers.FloatField()
        journey_pricing = serializers.DictField()
        pricing = serializers.DictField()

