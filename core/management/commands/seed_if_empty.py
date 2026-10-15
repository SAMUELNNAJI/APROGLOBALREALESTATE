"""Seed demo content on a fresh database.

Run on every deploy; fixtures are only loaded while the Property table is
empty, so existing data is never overwritten. On Render's free plan the
instance disk is recreated on each deploy, which re-seeds automatically.
"""
import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command

from core.models import Property


class Command(BaseCommand):
    help = "Load demo data (and optionally a superuser) if the database is empty."

    def handle(self, *args, **options):
        if Property.objects.exists():
            self.stdout.write("Database already has data; skipping demo fixture.")
        else:
            fixture = Path(settings.BASE_DIR) / "core" / "fixtures" / "initial_data.json"
            if fixture.exists():
                call_command("loaddata", str(fixture))
                self.stdout.write(self.style.SUCCESS(f"Loaded {fixture.name}."))
            else:
                self.stdout.write(self.style.WARNING(f"Fixture not found: {fixture}"))

        # Optional admin account for the custom dashboard (/dashboard/admin/),
        # created from environment variables on first boot only.
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not (username and password):
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": os.environ.get("DJANGO_SUPERUSER_EMAIL", ""),
                "is_superuser": True,
                "is_staff": True,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
        else:
            self.stdout.write(
                f"Superuser '{username}' already exists; password left unchanged."
            )
