from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rest_framework_simplejwt.tokens import AccessToken

API_USERNAME = "agentplace"


class Command(BaseCommand):
    help = "Print a JWT access token for the Agentplace agent."

    def handle(self, *args, **options):
        # The API user only authenticates with tokens, never a password.
        user, created = User.objects.get_or_create(username=API_USERNAME)
        if created:
            user.set_unusable_password()
            user.save()

        token = AccessToken.for_user(user)
        expires = datetime.fromtimestamp(token["exp"], tz=timezone.utc)
        self.stderr.write(f"Access token for '{API_USERNAME}', expires {expires:%Y-%m-%d %H:%M} UTC:")
        self.stdout.write(str(token))
