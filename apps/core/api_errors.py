"""Stable error reasons shared by explicit errors and DRF exceptions."""
import re


def error_reason(status):
    return {
        400: 'VALIDATION_ERROR', 401: 'AUTHENTICATION_REQUIRED',
        403: 'PERMISSION_DENIED', 404: 'NOT_FOUND', 409: 'REQUEST_CONFLICT',
        429: 'RATE_LIMITED',
    }.get(status, 'SERVER_ERROR' if status >= 500 else 'REQUEST_FAILED')


def error_details(details, status, reason=None):
    # Preserve field errors and existing semantic reasons (expiry, recovery, etc.).
    result = dict(details) if isinstance(details, dict) else (
        {'non_field_errors': details} if details is not None else {})
    current = result.get('reason')
    if not isinstance(current, str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}', current):
        # A serializer may have a user-editable field named reason. Retain its
        # validation error without confusing it with the machine-readable token.
        if current is not None:
            previous = result.get('non_field_errors')
            result['non_field_errors'] = [previous, current] if previous is not None else current
        result['reason'] = reason or error_reason(status)
    return result
