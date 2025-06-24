from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule


class Command(BaseCommand):
    help = 'Setup periodic task for sending departure notifications'

    def handle(self, *args, **options):
        schedule, created = IntervalSchedule.objects.get_or_create(
            period=IntervalSchedule.MINUTES,
            every=1,
        )

        task, created = PeriodicTask.objects.get_or_create(
            name='send_departure_notifications',
            defaults={
                'task': 'bookings.tasks.send_departure_notifications',
                'interval': schedule,
                'enabled': True,
            }
        )

        if not created:
            task.interval = schedule
            task.task = 'bookings.tasks.send_departure_notifications'
            task.enabled = True
            task.save()
            self.stdout.write(
                self.style.SUCCESS('Updated existing periodic task for departure notifications')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Created new periodic task for departure notifications')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Task "{task.name}" will run every {schedule.every} {schedule.period}'
            )
        ) 