from rest_framework import serializers
from trains.models import Train, Route, Stop, Schedule, Station


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


class StopSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = Stop
            fields = '__all__'

    class ModelSerializerWithStation(ModelSerializer):
        station = StationSerializers.ModelSerializer()

    class ModelSerializerWithRoute(ModelSerializer):
        route = RouteSerializers.ModelSerializer()

    class ModelSerializerWithRouteAndStation(ModelSerializer):
        station = StationSerializers.ModelSerializer()
        route = RouteSerializers.ModelSerializer()


class ScheduleSerializers:
    
    class ModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = Schedule
            fields = '__all__'

    class ModelSerializerWithRoute(ModelSerializer):
        route = RouteSerializers.ModelSerializer()
