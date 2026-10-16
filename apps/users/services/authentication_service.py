# backend/apps/users/services/authentication_service.py

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from ..models import User
from .login_security_service import LoginSecurityService


class AuthenticationService:

    # Session lifetime per role, in seconds.
    #
    # This constant is the ONLY place the policy lives. It is not
    # duplicated in settings.py — a duplicated policy is how the
    # value drifts. If you ever want this configurable from an
    # environment variable, wire it to a single settings key and
    # read it here, but do not fork the definition.
    #
    # Roles present in this deployment (see User.ROLE_CHOICES):
    #   • 'admin'     — 8 hours. Admins hold every capability and
    #                   handle database/backup operations; a shorter
    #                   session limits blast radius if a token leaks.
    #   • 'moderator' — 7 days.
    #   • 'member'    — falls through to settings.SESSION_COOKIE_AGE
    #                   (14 days) via request.session.set_expiry(None).
    SESSION_LIFETIME_BY_ROLE = {
        'admin':     8 * 60 * 60,        # 8 hours
        'moderator': 7 * 24 * 60 * 60,   # 7 days
        # 'member' → None → 14 days (SESSION_COOKIE_AGE)
    }

    @staticmethod
    def login_user(username, password, request=None):
        login_security = LoginSecurityService()
        ip = request.META.get('REMOTE_ADDR', '') if request else ''

        if login_security.is_blocked(ip, username):
            return None

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            login_security.record_attempt(ip, username, False)
            return None

        # Authentication may have read before an administrator changed this
        # account. Serialize eligibility/renewal with those account writers and
        # refuse a password reset or disable that committed before this lock.
        authenticated_hash = user.password
        backend = getattr(user, 'backend', None)
        with transaction.atomic():
            current = User.objects.select_for_update().filter(pk=user.pk).first()
            if current is None or not current.is_active or current.is_stub or current.password != authenticated_hash:
                user = None
            else:
                user = current
                user.renew_if_eligible()
                if user.is_expired:
                    user = None
                else:
                    user.last_login = timezone.now()
                    user.save(update_fields=['last_login'])
        if user is None:
            login_security.record_attempt(ip, username, False)
            return None
        if backend is not None:
            user.backend = backend
        login(request, user)

        if request is not None and hasattr(request, 'session'):
            lifetime = AuthenticationService.SESSION_LIFETIME_BY_ROLE.get(user.role)
            request.session.set_expiry(lifetime)

        login_security.record_attempt(ip, username, True)
        login_security.clear_failed_attempts_for_username(username)

        return user

    @staticmethod
    def logout_user(request):
        logout(request)

    @staticmethod
    def change_password(request, user, current_password, new_password):
        with transaction.atomic():
            # Recheck the current hash after any concurrent admin reset, and
            # avoid persisting stale roles, capabilities, or learning counters.
            user = User.objects.select_for_update().get(pk=user.pk)
            success, message = AuthenticationService._change_password_locked(
                user, current_password, new_password,
            )
        if success:
            update_session_auth_hash(request, user)
        return success, message

    @staticmethod
    def _change_password_locked(user, current_password, new_password):
        if not user.check_password(current_password):
            return False, 'كلمة المرور الحالية غير صحيحة'

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return False, ' '.join(e.messages)

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=['password', 'must_change_password'])

        return True, 'تم تغيير كلمة المرور بنجاح'
