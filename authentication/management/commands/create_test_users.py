from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Create test user and superuser for development'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create superuser
            if not User.objects.filter(username='admin').exists():
                superuser = User.objects.create_superuser(
                    username='admin',
                    email='admin@trainbooking.com',
                    password='admin123',
                    first_name='Admin',
                    last_name='User'
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ Created superuser: admin (password: admin123)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  Superuser "admin" already exists')
                )

            # Create test user
            if not User.objects.filter(username='testuser').exists():
                test_user = User.objects.create_user(
                    username='testuser',
                    email='testuser@trainbooking.com',
                    password='test123',
                    first_name='Test',
                    last_name='User'
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ Created test user: testuser (password: test123)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  Test user "testuser" already exists')
                )

            self.stdout.write('\n' + '='*50)
            self.stdout.write('🎯 LOGIN CREDENTIALS:')
            self.stdout.write('='*50)
            self.stdout.write('📝 Admin Panel: /admin/')
            self.stdout.write('   Username: admin')
            self.stdout.write('   Password: admin123')
            self.stdout.write('')
            self.stdout.write('👤 Test User:')
            self.stdout.write('   Username: testuser')
            self.stdout.write('   Password: test123')
            self.stdout.write('   Email: testuser@trainbooking.com')
            self.stdout.write('='*50) 