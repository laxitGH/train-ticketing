from datetime import time
from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from trains.services import JourneySearchService, TrainService
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.decorators import login_required
from utils.serializers import JourneyDateSerializer
from bookings.selectors import BookingSelectors
from trains.selectors import ScheduleSelectors
from utils.enums import BookingType, Weekday
from django.contrib.auth.models import User
from rest_framework.views import APIView
from utils.pagination import Paginator
from utils.queries import QueryUtils
from trains.models import Station


class JourneySearchInputSerializer(serializers.Serializer):
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    journey_date = JourneyDateSerializer(required=True)

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
            input=JourneySearchService.Input(
                journey_date=journey_date,
                source_station_code=source_station_code,
                destination_station_code=destination_station_code,
                schedule_query_options=schedule_query_options,
            )
        )

        journey_schedules = journey_search_service.search_journeys()
        serialized_data = JourneySearchService.OutputSerializer(journey_schedules, many=True)
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
@login_required
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
            input=JourneySearchService.Input(
                journey_date=serializer.validated_data['journey_date'],
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code'],
                schedule_query_options=schedule_query_options,
                booking_query_options=booking_query_options,
            )
        )

        journey_schedules = journey_search_service.search_journeys()
        journey_schedule = journey_schedules[0]
        serialized_data = JourneySearchService.OutputSerializer(journey_schedule)
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
        paginator = Paginator()
        train_service = TrainService()
        trains_queryset = train_service.get_trains_queryset()        
        paginated_trains = paginator.paginate_queryset(trains_queryset, request)
        serialized_data = TrainService.OutputSerializer(paginated_trains, many=True)
        return paginator.get_paginated_response(serialized_data.data)
    
    class StopPostInputSerializer(serializers.Serializer):
        order = serializers.IntegerField(required=True)
        distance_kms_from_source = serializers.FloatField(required=True)
        station_code = serializers.CharField(required=True, max_length=3)
        arrival_minutes_from_source = serializers.IntegerField(required=True)
        departure_minutes_from_source = serializers.IntegerField(required=True)

        def validate(self, data):
            if data['arrival_minutes_from_source'] >= data['departure_minutes_from_source']:
                raise serializers.ValidationError('Stop arrival minutes must be less than departure minutes')
            if data['order'] < 0:
                raise serializers.ValidationError('Order must be greater than 0')
            if data['distance_kms_from_source'] < 0:
                raise serializers.ValidationError('Distance must be greater than 0')
            if data['departure_minutes_from_source'] < 0:
                raise serializers.ValidationError('Stop departure minutes must be greater than 0')
            if data['arrival_minutes_from_source'] < 0:
                raise serializers.ValidationError('Stop arrival minutes must be greater than 0')
            return data

    class SchedulePostInputSerializer(serializers.Serializer):
        arrival_time = serializers.TimeField(required=True, format='%H:%M:%S')
        departure_time = serializers.TimeField(required=True, format='%H:%M:%S')
        weekday = serializers.ChoiceField(required=True, choices=Weekday.choices())

        def validate(self, data):
            if data['arrival_time'] <= data['departure_time']:
                raise serializers.ValidationError('Schedule arrival time must be greater than departure time')
            return data
    
    class RoutePostInputSerializer(serializers.Serializer):
        name = serializers.CharField(required=True)
        seats = serializers.JSONField(required=True)
        pricing = serializers.JSONField(required=True)
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['stops'] = TrainView.StopPostInputSerializer(many=True, required=True)
            self.fields['schedules'] = TrainView.SchedulePostInputSerializer(many=True, required=True)

        def validate_seats(self, value):
            if not value.get('general') or not value.get('tatkal'):
                raise serializers.ValidationError('Seats must be a dictionary with general and tatkal keys')
            return value
        
        def validate_pricing(self, value):
            if not value.get('general') or not value.get('tatkal'):
                raise serializers.ValidationError('Pricing must be a dictionary with general and tatkal keys')
            return value            
        
        def validate(self, data):
            stops = data['stops']
            if not stops or len(stops) < 2:
                raise serializers.ValidationError('At least 2 stations are required')
            
            sorted_stops = sorted(stops, key=lambda x: x['departure_minutes_from_source'])
            for idx, stop in enumerate(sorted_stops):
                stop_orders = [x['order'] for x in sorted_stops[0:idx]]
                if idx != 0 and stop['order'] <= max(stop_orders):
                    raise serializers.ValidationError('Stop order must be greater than previous stop order')
                
            stations = Station.objects.filter(code__in=[stop['station_code'] for stop in sorted_stops])
            stations = list(stations)
            if len(stations) != len(sorted_stops):
                raise serializers.ValidationError('Invalid station codes')

            for stop in sorted_stops:
                stop['station'] = next((station for station in stations if station.code == stop['station_code']), None)
            
            data['stops'] = sorted_stops
            data['stations'] = stations
            return data

    class TrainPostInputSerializer(serializers.Serializer):
        name = serializers.CharField(required=True)
        number = serializers.CharField(required=True)
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['route'] = TrainView.RoutePostInputSerializer(required=True)
        
    
    def post(self, request, *args, **kwargs):
        serializer = TrainView.TrainPostInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        train_service = TrainService()
        train_service.create_train(
            data=TrainService.CreateTrainInput.from_dict(serializer.validated_data)
        )
        
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': 'Train created successfully',
        })

