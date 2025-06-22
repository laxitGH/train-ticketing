from datetime import timedelta
from rest_framework import status
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from trains.services import TrainSearchService
from trains.selectors import RouteScheduleSelectors
from trains.model_utils import RouteScheduleModelUtils
from utils.enums import BookingType


class TrainSearchInputSerializer(serializers.Serializer):
    source_station_code = serializers.CharField(required=True)
    destination_station_code = serializers.CharField(required=True)
    journey_date = serializers.DateField(required=True, format='%Y-%m-%d')

    def validate_journey_date(self, value):
        today = timezone.now().date()
        max_date = today + timedelta(days=120)
        if value < today or value > max_date:
            raise serializers.ValidationError("Date cannot be in the past or more than 120 days from today")
        return value

@api_view(['GET'])
def train_search_view(request):
    serializer = TrainSearchInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    journey_date = serializer.validated_data['journey_date']
    source_station_code = serializer.validated_data['source_station_code']
    destination_station_code = serializer.validated_data['destination_station_code']
    print('inputs:', journey_date, source_station_code, destination_station_code)

    trains_data = TrainSearchService.search_trains(
        TrainSearchService.Input(
            journey_date=journey_date,
            source_station_code=source_station_code,
            destination_station_code=destination_station_code
        )
    )

    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': trains_data,
    })


class TrainSeatAvailabilityInputSerializer(serializers.Serializer):
    schedule_id = serializers.CharField(required=True)
    journey_date = serializers.DateField(required=True, format='%Y-%m-%d')
    booking_type = serializers.ChoiceField(required=True, choices=[BookingType.GENERAL.value, BookingType.TATKAL.value])

@api_view(['GET'])
def train_seat_availability_view(request):
    serializer = TrainSeatAvailabilityInputSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    schedule_id = serializer.validated_data['schedule_id']
    journey_date = serializer.validated_data['journey_date']
    booking_type = serializer.validated_data['booking_type']

    main_filters = dict(id=schedule_id)
    booking_filters = dict(type=booking_type)
    route_schedule = RouteScheduleSelectors.get_schedule_details_queryset(
        booking_filters=booking_filters,
        journey_date=journey_date,
        main_filters=main_filters,
    ).first()

    if not route_schedule:
        return Response({
            'status': False,
            'status_code': status.HTTP_404_NOT_FOUND,
            'result': 'Schedule not found',
        })
    
    bookings_of_schedule = getattr(route_schedule, 'bookings_of_schedule', [])
    seat_availability_data = RouteScheduleModelUtils.get_seat_availability_data(
        schedule=route_schedule,
        bookings=bookings_of_schedule,
        journey_date=journey_date,
    )
    booking_windows_data = RouteScheduleModelUtils.get_booking_windows_data(
        schedule=route_schedule,
        journey_date=journey_date,
    )

    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': {
            'seat_availability_data': seat_availability_data.to_dict(),
            'booking_windows_data': booking_windows_data.to_dict(),
        },
    })