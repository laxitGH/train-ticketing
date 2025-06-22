from django.utils import timezone
from rest_framework import status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from trains.services import JourneySearchService
from utils.enums import BookingType, BookingStatus
from utils.serializers import JourneyDateSerializer
from bookings.serializers import BookingsSerializers
from trains.dataclasses import JourneySearchServiceDataclasses
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from utils.queries import QueryUtils
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
@QueryUtils.log_queries
def booking_create_view(request):
    user: User = request.user
    serializer = BookingCreateInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    booking_type = serializer.validated_data['type']
    journey_date = serializer.validated_data['journey_date']
    with transaction.atomic():
        journey_search_service = JourneySearchService(
            input=JourneySearchServiceDataclasses.Input(
                journey_date=journey_date,
                source_station_code=serializer.validated_data['source_station_code'],
                destination_station_code=serializer.validated_data['destination_station_code']
            )
        )

        journey_schedules = journey_search_service.search_journeys(
            main_filters=dict(id=serializer.validated_data['schedule_id']),
        )

        journey_schedule = journey_schedules[0]
        if booking_type == BookingType.GENERAL.value:
            if not journey_schedule.booking_window_details['general_booking_open']:
                return Response({
                    'status': False,
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'result': 'General booking window not open',
                })
        elif booking_type == BookingType.TATKAL.value:
            if not journey_schedule.booking_window_details['tatkal_booking_open']:
                return Response({
                    'status': False,
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'result': 'Tatkal booking window not open',
                })
        
        confirmation_datetime = None
        if booking_type == BookingType.GENERAL.value:
            if journey_schedule.seat_details['available_seats'][BookingType.GENERAL.value] > 0:
                booking_status = BookingStatus.CONFIRMED.value
                confirmation_datetime = timezone.now()
            else:
                booking_status = BookingStatus.WAITING.value
        elif booking_type == BookingType.TATKAL.value:
            if journey_schedule.seat_details['available_seats'][BookingType.TATKAL.value] > 0:
                booking_status = BookingStatus.CONFIRMED.value
                confirmation_datetime = timezone.now()
            else:
                raise ValueError('No tatkal seats available')
        
        booking = Booking.objects.create(
            user=user,
            journey_date=journey_date,
            schedule=journey_schedule,
            from_stop=journey_schedule.source_stop,
            to_stop=journey_schedule.destination_stop,
            amount=journey_schedule.general_details['pricing'][booking_type],
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


@api_view(['POST'])
@login_required
@QueryUtils.log_queries
def booking_cancel_view(request, booking_id: int):
    with transaction.atomic():
        booking = Booking.objects.get(
            user=request.user,
            id=booking_id,
        )

        if booking.status == BookingStatus.CANCELLED.value:
            return Response({
                'status': False,
                'status_code': status.HTTP_400_BAD_REQUEST,
                'result': 'Booking already cancelled',
            })
        if booking.type == BookingType.TATKAL.value:
            if booking.status == BookingStatus.CONFIRMED.value:
                return Response({
                    'status': False,
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'result': 'Tatkal booking cannot be cancelled',
                })
        
        now = timezone.now()
        if booking.status == BookingStatus.CONFIRMED.value:
            oldest_waiting_booking = Booking.objects.filter(
                journey_date=booking.journey_date,
                status=BookingStatus.WAITING.value,
                type=BookingType.GENERAL.value,
                from_stop=booking.from_stop,
                schedule=booking.schedule,
                to_stop=booking.to_stop,
            ).order_by('created_at').first()
            if oldest_waiting_booking:
                oldest_waiting_booking.status = BookingStatus.CONFIRMED.value
                oldest_waiting_booking.confirmation_datetime = now
                oldest_waiting_booking.save()

        booking.status = BookingStatus.CANCELLED.value
        booking.cancellation_datetime = now
        booking.save()

        serialized_data = BookingsSerializers.ModelSerializer(booking).data
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': serialized_data,
        })
    

@api_view(['GET'])
@login_required
@QueryUtils.log_queries
def booking_details_view(request, booking_id: int):
    with transaction.atomic():
        booking = Booking.objects.get(
            user=request.user,
            id=booking_id,
        )

        if booking.status == BookingStatus.WAITING.value:
            waiting_bookings = Booking.objects.filter(
                journey_date=booking.journey_date,
                status=BookingStatus.WAITING.value,
                type=BookingType.GENERAL.value,
                from_stop=booking.from_stop,
                schedule=booking.schedule,
                to_stop=booking.to_stop,
            ).order_by('created_at')
            waiting_position = list(waiting_bookings).index(booking) + 1
        else:
            waiting_position = None

        serialized_data = BookingsSerializers.ModelSerializer(booking).data
        serialized_data['waiting_position'] = waiting_position
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': serialized_data,
        })


@api_view(['GET'])
@login_required
@QueryUtils.log_queries
def user_bookings_list_view(request):
    user: User = request.user
    user_bookings = Booking.objects.filter(user=user).order_by('-created_at')
    serialized_data = BookingsSerializers.ModelSerializer(user_bookings, many=True).data
    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': serialized_data,
    })