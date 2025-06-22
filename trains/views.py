from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from trains.serializers import RouteScheduleSerializers, RouteSerializers, RouteStationSerializers
from trains.services import TrainSearchService, TrainAvailabilityStatusService
from utils.serializers import JourneyDateSerializer
from django.contrib.auth.models import User
from utils.queries import QueryUtils
from utils.enums import BookingType


class TrainSearchInputSerializer(serializers.Serializer):
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    journey_date = JourneyDateSerializer(required=True)

class TrainSearchOutputSerializer(serializers.Serializer):
    route = RouteSerializers.ModelSerializerWithTrain()
    source_route_station = RouteStationSerializers.ModelSerializerWithStation()
    destination_route_station = RouteStationSerializers.ModelSerializerWithStation()
    route_stations = RouteStationSerializers.ModelSerializerWithRouteAndStation(many=True)
    seat_availability_data = RouteScheduleSerializers.SeatAvailabilitySerializer()
    booking_windows_data = RouteScheduleSerializers.BookingWindowsSerializer()
    journey_duration_minutes = serializers.IntegerField()
    journey_distance_kms = serializers.FloatField()
    general_pricing = serializers.FloatField()
    tatkal_pricing = serializers.FloatField()

@api_view(['GET'])
@QueryUtils.log_queries
def train_search_view(request):
    user: User = request.user
    serializer = TrainSearchInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try :
        train_schedules = TrainSearchService.search_trains(
            TrainSearchService.Input(
                journey_date=serializer.validated_data['journey_date'],
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code']
            )
        )
    except Exception as e:
        return Response({
            'status': False,
            'status_code': status.HTTP_400_BAD_REQUEST,
            'result': str(e),
        })

    serialized_data = TrainSearchOutputSerializer(train_schedules, many=True)
    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': serialized_data.data,
    })


class TrainAvailabilityStatusInputSerializer(serializers.Serializer):
    journey_date = JourneyDateSerializer(required=True)
    schedule_id = serializers.IntegerField(required=True)
    booking_type = serializers.ChoiceField(required=True, choices=[BookingType.GENERAL.value, BookingType.TATKAL.value])
    destination_station_code = serializers.CharField(required=True)
    source_station_code = serializers.CharField(required=True)

class TrainAvailabilityStatusOutputSerializer(serializers.Serializer):
    booking_windows_data = RouteScheduleSerializers.BookingWindowsSerializer()
    seat_availability_data = RouteScheduleSerializers.SeatAvailabilitySerializer()

@api_view(['GET'])
@QueryUtils.log_queries
def train_availability_status_view(request):
    user: User = request.user
    serializer = TrainAvailabilityStatusInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try :
        train_availability = TrainAvailabilityStatusService.get_seat_availability(
            TrainAvailabilityStatusService.Input(
                journey_date=serializer.validated_data['journey_date'],
                schedule_id=serializer.validated_data['schedule_id'],
                booking_type=serializer.validated_data['booking_type'],
                destination_station_code=serializer.validated_data['destination_station_code'],
                source_station_code=serializer.validated_data['source_station_code']
            )
        )
    except Exception as e:
        return Response({
            'status': False,
            'status_code': status.HTTP_400_BAD_REQUEST,
            'result': str(e),
        })

    serialized_data = TrainAvailabilityStatusOutputSerializer(train_availability)
    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': serialized_data.data,
    })