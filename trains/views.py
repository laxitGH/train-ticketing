from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from trains.services import JourneySearchService, TrainService
from trains.serializers import RouteSerializers, StopSerializers, ScheduleSerializers, TrainSerializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from trains.dataclasses import JourneySearchServiceDataclasses
from utils.serializers import JourneyDateSerializer
from bookings.selectors import BookingSelectors
from trains.selectors import ScheduleSelectors
from django.contrib.auth.models import User
from rest_framework.views import APIView
from utils.queries import QueryUtils
from utils.enums import BookingType


class JourneySearchInputSerializer(serializers.Serializer):
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    journey_date = JourneyDateSerializer(required=True)

class JourneySearchOutputSerializer(ScheduleSerializers.ModelSerializer):
    route = RouteSerializers.ModelSerializerWithTrain()
    source_stop = StopSerializers.ModelSerializerWithStation()
    destination_stop = StopSerializers.ModelSerializerWithStation()
    stops = StopSerializers.ModelSerializerWithRouteAndStation(many=True)
    booking_window_details = serializers.SerializerMethodField()
    general_details = serializers.SerializerMethodField()
    seat_details = serializers.SerializerMethodField()

    def get_booking_window_details(self, obj):
        return obj.booking_window_details.to_dict()
    
    def get_general_details(self, obj):
        return obj.general_details.to_dict()
    
    def get_seat_details(self, obj):    
        return obj.seat_details.to_dict()

@api_view(['GET'])
@QueryUtils.log_queries
def journey_search_view(request):
    user: User = request.user
    serializer = JourneySearchInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try :
        journey_date = serializer.validated_data['journey_date']
        source_station_code = serializer.validated_data['source_station_code']
        destination_station_code = serializer.validated_data['destination_station_code']
        schedule_query_options = ScheduleSelectors.Options(
            filters=dict(route__stops_of_route__station__code__in=[source_station_code, destination_station_code]),
        )

        journey_search_service = JourneySearchService(
            input=JourneySearchServiceDataclasses.Input(
                journey_date=journey_date,
                source_station_code=source_station_code,
                destination_station_code=destination_station_code,
                schedule_query_options=schedule_query_options,
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
    booking_type = serializers.ChoiceField(required=True, choices=BookingType.choices()) 

@api_view(['GET'])
@QueryUtils.log_queries
def journey_details_view(request):
    user: User = request.user
    serializer = JourneyDetailsInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try :
        schedule_query_options = ScheduleSelectors.Options(
            filters=dict(id=serializer.validated_data['schedule_id']),
        )
        booking_query_options = BookingSelectors.Options(
            filters=dict(type=serializer.validated_data['booking_type']),
        )

        journey_search_service = JourneySearchService(
            input=JourneySearchServiceDataclasses.Input(
                journey_date=serializer.validated_data['journey_date'],
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code'],
                schedule_query_options=schedule_query_options,
                booking_query_options=booking_query_options,
            )
        )

        journey_schedules = journey_search_service.search_journeys()
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
    

class TrainView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        user: User = request.user
        journey_service = TrainService()
        trains = journey_service.get_all_trains()
        serialized_data = TrainSerializers.ModelSerializer(trains, many=True)
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': serialized_data.data,
        })
    
    def post(self, request, *args, **kwargs):
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': 'Hello, world!',
        })
    
    def put(self, request, *args, **kwargs):
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': 'Hello, world!',
        })
