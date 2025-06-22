from django.utils import timezone
from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from utils.enums import BookingType, BookingStatus
from utils.serializers import JourneyDateSerializer
from trains.services import TrainAvailabilityStatusService
from bookings.serializers import BookingsSerializers
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from bookings.models import Booking
from django.db import transaction


class BookingCreateInputSerializer(serializers.Serializer):
    journey_date = JourneyDateSerializer(required=True)
    type = serializers.ChoiceField(required=True, choices=[BookingType.GENERAL.value, BookingType.TATKAL.value])
    destination_station_code = serializers.CharField(required=True)
    source_station_code = serializers.CharField(required=True)
    schedule_id = serializers.IntegerField(required=True)

@api_view(['POST'])
@login_required
def booking_create_view(request):
    user: User = request.user
    serializer = BookingCreateInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        train_availability = TrainAvailabilityStatusService.get_seat_availability(
            TrainAvailabilityStatusService.Input(
                booking_type=serializer.validated_data['type'],
                schedule_id=serializer.validated_data['schedule_id'],
                journey_date=serializer.validated_data['journey_date'],
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code'],
            )
        )

        booking_type = serializer.validated_data['type']
        if booking_type == BookingType.GENERAL.value:
            if not train_availability.booking_windows_data.general_booking_open:
                return Response({
                    'status': False,
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'result': 'General booking window not open',
                })
        elif booking_type == BookingType.TATKAL.value:
            if not train_availability.booking_windows_data.tatkal_booking_open:
                return Response({
                    'status': False,
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'result': 'Tatkal booking window not open',
                })
        
        confirmation_datetime = None
        if booking_type == BookingType.GENERAL.value:
            if train_availability.seat_availability_data.available_general_seats > 0:
                booking_status = BookingStatus.CONFIRMED.value
                confirmation_datetime = timezone.now()
            else:
                booking_status = BookingStatus.WAITING.value
        elif booking_type == BookingType.TATKAL.value:
            if train_availability.seat_availability_data.available_tatkal_seats > 0:
                booking_status = BookingStatus.CONFIRMED.value
                confirmation_datetime = timezone.now()
            else:
                raise ValueError('No tatkal seats available')
        
        booking = Booking.objects.create(
            user=request.user,
            journey_date=serializer.validated_data['journey_date'],
            from_route_station=train_availability.source_route_station,
            to_route_station=train_availability.destination_route_station,
            route_schedule=train_availability.seat_availability_data.route_schedule,
            amount=train_availability.seat_availability_data.journey_pricing[booking_type],
            confirmation_datetime=confirmation_datetime,
            status=booking_status,
            type=booking_type,
        )

        serialized_data = BookingsSerializers.ModelSerializer(booking).data
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': serialized_data,
        })


class BookingCancelInputSerializer(serializers.Serializer):
    pass

@api_view(['POST'])
def booking_cancel_view(request):
    serializer = BookingCancelInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookingDetailsInputSerializer(serializers.Serializer):
    pass

@api_view(['GET'])
def booking_details_view(request):
    serializer = BookingDetailsInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserBookingsListInputSerializer(serializers.Serializer):
    pass

@api_view(['GET'])
def user_bookings_list_view(request):
    serializer = UserBookingsListInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)