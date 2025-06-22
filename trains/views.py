from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from trains.services import JourneySearchService
from trains.serializers import RouteSerializers, StopSerializers
from trains.dataclasses import JourneySearchServiceDataclasses
from utils.serializers import JourneyDateSerializer
from django.contrib.auth.models import User
from utils.queries import QueryUtils
from utils.enums import BookingType


class JourneySearchInputSerializer(serializers.Serializer):
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    journey_date = JourneyDateSerializer(required=True)

class JourneySearchOutputSerializer(serializers.Serializer):
    route = RouteSerializers.ModelSerializerWithTrain()
    source_stop = StopSerializers.ModelSerializerWithStation()
    destination_stop = StopSerializers.ModelSerializerWithStation()
    stops = StopSerializers.ModelSerializerWithRouteAndStation(many=True)
    booking_window_details = serializers.DictField()
    general_details = serializers.DictField()
    seat_details = serializers.DictField()

@api_view(['GET'])
@QueryUtils.log_queries
def journey_search_view(request):
    user: User = request.user
    serializer = JourneySearchInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try :
        journey_search_service = JourneySearchService(
            input=JourneySearchServiceDataclasses.Input(
                journey_date=serializer.validated_data['journey_date'],
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code']
            )
        )

        journey_schedules = journey_search_service.search_journeys()
        serialized_data = JourneySearchOutputSerializer(journey_schedules, many=True)
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': serialized_data.data,
        })
    except Exception as e:
        return Response({
            'status': False,
            'status_code': status.HTTP_400_BAD_REQUEST,
            'result': str(e),
        })


class JourneyDetailsInputSerializer(serializers.Serializer):
    journey_date = JourneyDateSerializer(required=True)
    schedule_id = serializers.IntegerField(required=True)
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    booking_type = serializers.ChoiceField(required=True, choices=[BookingType.GENERAL.value, BookingType.TATKAL.value])

@api_view(['GET'])
@QueryUtils.log_queries
def journey_details_view(request):
    user: User = request.user
    serializer = JourneyDetailsInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try :
        journey_search_service = JourneySearchService(
            input=JourneySearchServiceDataclasses.Input(
                journey_date=serializer.validated_data['journey_date'],
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code']
            )
        )

        journey_schedules = journey_search_service.search_journeys(
            main_filters=dict(id=serializer.validated_data['schedule_id']),
            booking_filters=dict(type=serializer.validated_data['booking_type']),
        )

        journey_schedule = journey_schedules[0]
        serialized_data = JourneySearchOutputSerializer(journey_schedule)
        data = {
            "seat_details": serialized_data.data['seat_details'],
            "general_details": serialized_data.data['general_details'],
            "booking_window_details": serialized_data.data['booking_window_details'],
        }

        return Response({
            'status': True,
            'result': data,
            'status_code': status.HTTP_200_OK,
        })
    except Exception as e:
        return Response({
            'status': False,
            'status_code': status.HTTP_400_BAD_REQUEST,
            'result': str(e),
        })