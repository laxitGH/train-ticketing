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
from rest_framework.decorators import action
from django.contrib.auth.models import User
from rest_framework.views import APIView
from utils.pagination import Paginator
from utils.queries import QueryUtils
from trains.models import Station
from django.db import transaction


class JourneySearchInputSerializer(serializers.Serializer):
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    journey_date = JourneyDateSerializer(required=True)

@api_view(['GET'])
@QueryUtils.log_queries
def journey_search_view(request):
    try :
        user: User = request.user
        serializer = JourneySearchInputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
    try :
        user: User = request.user
        serializer = JourneyDetailsInputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
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
        
    class StopListInputSerializer(serializers.ListSerializer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.child = TrainView.StopPostInputSerializer()

        def validate(self, value):
            if not value or len(value) < 2:
                raise serializers.ValidationError('At least 2 stations are required')
            
            sorted_stops = sorted(value, key=lambda x: x['departure_minutes_from_source'])
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

            return value

    class SchedulePostInputSerializer(serializers.Serializer):
        arrival_time = serializers.TimeField(required=True, format='%H:%M:%S')
        departure_time = serializers.TimeField(required=True, format='%H:%M:%S')
        weekday = serializers.ChoiceField(required=True, choices=Weekday.choices())

        def validate(self, data):
            if data['arrival_time'] <= data['departure_time']:
                raise serializers.ValidationError('Schedule arrival time must be greater than departure time')
            return data
        
    class ScheduleListInputSerializer(serializers.ListSerializer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.child = TrainView.SchedulePostInputSerializer()
    
    class RoutePostInputSerializer(serializers.Serializer):
        name = serializers.CharField(required=True)
        seats = serializers.JSONField(required=True)
        pricing = serializers.JSONField(required=True)
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['stops'] = TrainView.StopListInputSerializer(required=True)
            self.fields['schedules'] = TrainView.ScheduleListInputSerializer(required=True)

        def validate_seats(self, value):
            if not value.get('general') or not value.get('tatkal'):
                raise serializers.ValidationError('Seats must be a dictionary with general and tatkal keys')
            return value
        
        def validate_pricing(self, value):
            if not value.get('general') or not value.get('tatkal'):
                raise serializers.ValidationError('Pricing must be a dictionary with general and tatkal keys')
            return value

    class TrainPostInputSerializer(serializers.Serializer):
        name = serializers.CharField(required=True)
        number = serializers.CharField(required=True)
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['route'] = TrainView.RoutePostInputSerializer(required=True)
    
    def post(self, request, *args, **kwargs):
        try :
            serializer = TrainView.TrainPostInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                train_service = TrainService()
                train = train_service.get_or_create_train(
                    name=serializer.validated_data['name'],
                    number=serializer.validated_data['number'],
                )

                route = serializer.validated_data['route']
                train_service.add_routes_to_train(
                    route_data=TrainService.CreateRouteInput.from_dict(route),
                    train=train,
                )
            
            return Response({
                'status': True,
                'status_code': status.HTTP_200_OK,
                'result': 'Train created successfully',
            })
        except Exception as e:
            return Response({
                'status': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'result': str(e),
            })
    
    class RemoveRouteInputSerializer(serializers.Serializer):
        route_id = serializers.IntegerField(required=True)
    
    @action(detail=True, methods=['post'], url_path='remove-route')
    def remove_route_from_train(self, request, *args, **kwargs):
        try :
            serializer = TrainView.RemoveRouteInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                route_id = serializer.validated_data['route_id']
                train_service = TrainService()
                train_service.remove_route_from_train(route_id=route_id)

            return Response({
                'status': True,
                'status_code': status.HTTP_200_OK,
                'result': 'Route removed successfully',
            })
        except Exception as e:
            return Response({
                'status': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'result': str(e),
            })
    
    class AddScheduleInputSerializer(serializers.Serializer):
        route_id = serializers.IntegerField(required=True)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['schedule'] = TrainView.SchedulePostInputSerializer(required=True)
    
    @action(detail=True, methods=['post'], url_path='add-schedule')
    def add_schedule_to_route(self, request, *args, **kwargs):
        try :
            serializer = TrainView.AddScheduleInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                train_service = TrainService()
                train = train_service.get_or_create_train(
                    name=serializer.validated_data['name'],
                    number=serializer.validated_data['number'],
                )

                schedule = serializer.validated_data['schedule']
                train_service.add_schedule_to_route(
                    train=train,
                    route_id=serializer.validated_data['route_id'],
                    schedule=TrainService.CreateScheduleInput.from_dict(schedule),
                )
            
            return Response({
                'status': True,
                'status_code': status.HTTP_200_OK,
                'result': 'Schedule added successfully',
            })
        except Exception as e:
            return Response({
                'status': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'result': str(e),
            })
        
    class RemoveScheduleInputSerializer(serializers.Serializer):
        schedule_id = serializers.IntegerField(required=True)

    @action(detail=True, methods=['post'], url_path='remove-schedule')
    def remove_schedule_from_route(self, request, *args, **kwargs):
        try: 
            serializer = TrainView.RemoveScheduleInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                train_service = TrainService()
                train_service.remove_schedule_from_route(
                    schedule_id=serializer.validated_data['schedule_id'],
                )
            
            return Response({
                'status': True,
                'status_code': status.HTTP_200_OK,
                'result': 'Schedule removed successfully',
            })  
        except Exception as e:
            return Response({
                'status': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'result': str(e),
            })
        
    class UpdateStopsInputSerializer(serializers.Serializer):
        route_id = serializers.IntegerField(required=True)
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['stops'] = TrainView.StopListInputSerializer(required=True)

    @action(detail=True, methods=['post'], url_path='update-stops')
    def update_stops_of_route(self, request, *args, **kwargs):
        try :
            serializer = TrainView.UpdateStopsInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                train_service = TrainService()
                train_service.update_stops_of_route(
                    route_id=serializer.validated_data['route_id'],
                    stops=[
                        TrainService.CreateStopInput.from_dict(stop)
                        for stop in serializer.validated_data['stops']
                    ],
                )
            
            return Response({
                'status': True, 
                'status_code': status.HTTP_200_OK,
                'result': 'Stops updated successfully',
            })
        except Exception as e:
            return Response({
                'status': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'result': str(e),
            })
