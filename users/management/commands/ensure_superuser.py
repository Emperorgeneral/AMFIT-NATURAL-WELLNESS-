import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update superuser from environment variables."

    def handle(self, *args, **options):
        email = os.getenv("ADMIN_LOGIN_EMAIL") or os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("ADMIN_LOGIN_PASSWORD") or os.getenv("DJANGO_SUPERUSER_PASSWORD")
        username = os.getenv("ADMIN_LOGIN_USERNAME") or os.getenv("DJANGO_SUPERUSER_USERNAME")

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "Skipping superuser bootstrap: ADMIN_LOGIN_EMAIL and ADMIN_LOGIN_PASSWORD are not set."
                )
            )
            return

        User = get_user_model()

        if not username:
            username = email.split("@")[0]

        defaults = {
            "email": email,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }

        user, created = User.objects.get_or_create(username=username, defaults=defaults)

        if not created:
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True

        user.set_password(password)
        user.save()

        message = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{message} superuser '{username}' from env vars."))
