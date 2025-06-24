from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from utils.enums import BookingStatus
from datetime import timedelta
from .models import Booking


def send_booking_notification_email(booking: Booking):
    try:
        train = booking.schedule.route.train
        subject = f"Train Departure Reminder - {train.name} ({train.number})"
        message = f"""
Dear {booking.user.first_name or booking.user.username},
Your train is departing in 30 minutes!
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            fail_silently=False,
        )
        
        print(f"Notification email sent for booking {booking.id}")
        return True
        
    except Exception as e:
        print(f"Failed to send email for booking {booking.id}: {str(e)}")
        raise 


@shared_task
def send_departure_notifications():
    """
    Periodic task that runs every minute to check for bookings 
    that need departure notifications (30 minutes before departure).
    """
    now = timezone.now()
    
    target_time = now + timedelta(minutes=30)
    target_time_only = target_time.time()
    target_date = target_time.date()
    
    weekday = target_time.strftime('%a').upper()[:3]
    bookings_to_notify = Booking.objects.filter(
        journey_date=target_date,
        schedule__weekday=weekday,
        schedule__departure_time__hour=target_time_only.hour,
        schedule__departure_time__minute=target_time_only.minute,
        status=BookingStatus.CONFIRMED.value,
        cancellation_datetime__isnull=True,
        notification_sent=False
    ).select_related(
        'user', 'schedule', 'schedule__route', 'schedule__route__train',
        'from_stop', 'from_stop__station', 'to_stop', 'to_stop__station'
    )
    
    notifications_sent = 0
    
    for booking in bookings_to_notify:
        try:
            seat_number = f"{booking.type.upper()}-{booking.id}"
            send_booking_notification_email(booking, seat_number)
            booking.notification_sent = True
            booking.save(update_fields=['notification_sent'])
            notifications_sent += 1
        except Exception as e:
            print(f"Failed to send notification for booking {booking.id}: {str(e)}")
    
    print(f"Sent {notifications_sent} departure notifications")
