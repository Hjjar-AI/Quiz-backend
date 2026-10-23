"""Session authentication with a typed, pre-dispatch CSRF rejection."""
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied


class CsrfFailed(PermissionDenied):
    default_code = 'csrf_failed'


class ApiSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        try:
            super().enforce_csrf(request)
        except PermissionDenied as exc:
            # The exception is caught only at the CSRF check, before view dispatch.
            raise CsrfFailed(detail=exc.detail) from exc
