"""Caller-owned login sessions. Handles never expose bearer session keys."""
from importlib import import_module
import re

from django.conf import settings
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
from django.db import transaction
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.throttles import AdminPasswordRateThrottle
from apps.core.utils import api_error, api_success
from ..models import ActiveSession, User
from ..services import AuthenticationService


class RevokeSessionSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


def _handle(user_id, session_key):
    return salted_hmac('mukhtabir.own-session', f'{user_id}:{session_key}', algorithm='sha256').hexdigest()


def _store():
    engine = settings.SESSION_ENGINE
    if engine == 'django.contrib.sessions.backends.signed_cookies':
        return None  # Stateless cookies cannot be individually revoked.
    return import_module(engine).SessionStore


def _live(store_class, row, user):
    data = store_class(session_key=row.session_id).load()
    hashes = [user.get_session_auth_hash()]
    fallback = getattr(user, 'get_session_auth_fallback_hash', None)
    if fallback:
        hashes.extend(fallback())
    return str(data.get(SESSION_KEY, '')) == str(user.pk) and any(
        constant_time_compare(data.get(HASH_SESSION_KEY, ''), value) for value in hashes
    )


class OwnSessionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        store = _store()
        if store is None:
            return api_error('إدارة الجلسات غير مدعومة مع إعداد الجلسة الحالي', 501)
        rows = ActiveSession.objects.filter(user=request.user).order_by('-last_seen')
        items = [{
            'id': _handle(request.user.pk, row.session_id),
            'is_current': row.session_id == request.session.session_key,
            'ip': row.ip,
            'user_agent': row.user_agent or '',
            'last_seen': row.last_seen,
        } for row in rows if _live(store, row, request.user)]
        # Presence tracking is periodic and best effort. Include this known live session.
        current = request.session.session_key
        if current and not any(item['is_current'] for item in items):
            items.insert(0, {
                'id': _handle(request.user.pk, current), 'is_current': True,
                'ip': request.META.get('REMOTE_ADDR'),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
                'last_seen': timezone.now(),
            })
        return api_success(data={'items': items, 'total': len(items)})


class RevokeOwnSessionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AdminPasswordRateThrottle]

    def post(self, request, handle):
        if not re.fullmatch(r'[0-9a-f]{64}', handle):
            return api_error('الجلسة غير موجودة', 404)
        store = _store()
        if store is None:
            return api_error('إدارة الجلسات غير مدعومة مع إعداد الجلسة الحالي', 501)
        body = RevokeSessionSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if not user.check_password(body.validated_data['current_password']):
                return api_error('كلمة المرور الحالية غير صحيحة', 400)
            current = request.session.session_key
            is_current = bool(current and constant_time_compare(_handle(user.pk, current), handle))
            target = current if is_current else None
            rows = ActiveSession.objects.select_for_update().filter(user=user)
            for row in rows:
                if constant_time_compare(_handle(user.pk, row.session_id), handle):
                    target = row.session_id
                    break
            if not target:
                return api_error('الجلسة غير موجودة', 404)
            # SessionStore honours the configured database/cache/file backend.
            store(session_key=target).delete()
            ActiveSession.objects.filter(user=user, session_id=target).delete()
            if is_current:
                AuthenticationService.logout_user(request)
        return api_success(data={'revoked': True, 'is_current': is_current}, message='تم إنهاء الجلسة')
