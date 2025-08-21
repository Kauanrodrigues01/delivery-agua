from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decouple import config

SUPERUSER_USERNAME = config('SUPERUSER_USERNAME', default='admin', cast=str)
SUPERUSER_EMAIL = config('SUPERUSER_EMAIL', default='admin@gmail.com', cast=str)
SUPERUSER_PASSWORD = config('SUPERUSER_PASSWORD', default='admin', cast=str)


class Command(BaseCommand):
    help = 'Create a superuser'

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(
            username=SUPERUSER_USERNAME,
            email=SUPERUSER_EMAIL
        )

        if created:
            user.set_password(SUPERUSER_PASSWORD)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))
