import hmac

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ApiClient:
    """The single trusted caller (the Agentplace store agent)."""

    is_authenticated = True


class BearerTokenAuthentication(BaseAuthentication):
    """Accepts `Authorization: Bearer <token>` matching STORE_API_TOKEN."""

    keyword = "Bearer"

    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION")
        if not header:
            return None  # Reported as NotAuthenticated (401) by the permission check.

        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != self.keyword.lower():
            raise AuthenticationFailed()

        expected = settings.STORE_API_TOKEN
        if not expected or not hmac.compare_digest(parts[1].encode(), expected.encode()):
            raise AuthenticationFailed()

        return ApiClient(), None

    def authenticate_header(self, request):
        # Returning a value makes DRF answer 401 instead of 403.
        return self.keyword
