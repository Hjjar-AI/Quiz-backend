"""Bounded offline operation metadata, never request bodies or learning content."""
import logging
import time
import uuid


logger = logging.getLogger('django.server.offline')


class OfflineOperationLoggingMixin:
    def dispatch(self, request, *args, **kwargs):
        started = time.perf_counter()
        operation_id = uuid.uuid4().hex
        status = 500
        reason = 'UNEXPECTED_FAILURE'
        failure_type = '-'
        try:
            response = super().dispatch(request, *args, **kwargs)
            status = response.status_code
            reasons = {400: 'VALIDATION_REJECTED', 401: 'AUTHENTICATION_REQUIRED',
                       403: 'PERMISSION_DENIED', 404: 'NOT_AVAILABLE', 409: 'CONFLICT',
                       429: 'THROTTLED'}
            reason = getattr(self.request, '_offline_reason',
                             'SUCCESS' if status < 400 else reasons.get(status, 'REQUEST_FAILED'))
            response['X-Offline-Operation-ID'] = operation_id
            return response
        except Exception as failure:
            failure_type = type(failure).__name__
            raise
        finally:
            current_request = getattr(self, 'request', None)
            completion = getattr(current_request, '_offline_completion_reference', '-')
            if failure_type == '-':
                failure_type = getattr(current_request, '_offline_failure_type', '-')
            log = logger.warning if status >= 400 else logger.info
            log('offline operation=%s operation_id=%s completion_ref=%s status=%s reason=%s duration_ms=%.1f failure_type=%s',
                type(self).__name__, operation_id, completion, status, reason,
                (time.perf_counter() - started) * 1000, failure_type)
